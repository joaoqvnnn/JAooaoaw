import json

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    add_to_cart, cart_total_qty, count_stock, get_cart, get_or_create_user,
    get_product, remove_cart_item, upsert_state,
)
from keyboards import (
    kb_cart, kb_cart_empty, kb_cart_remove, kb_purchase_confirm,
)
from texts import fmt_brl, get_text


def effective_price(p) -> float:
    if p.promo_price is not None and float(p.promo_price) > 0:
        return float(p.promo_price)
    return float(p.price)


async def add_product_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    prod_id = int(q.data.split(":")[2])
    user = await get_or_create_user(update.effective_user)
    prod = await get_product(prod_id)

    if not prod or not prod.active or not prod.visible:
        await q.answer("❌ Produto indisponível.", show_alert=True)
        return

    await add_to_cart(user.telegram_id, prod_id, 1)
    await q.answer("✓ Produto adicionado ao carrinho!")


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    items = await get_cart(user.telegram_id)

    if not items:
        await q.edit_message_text(
            await get_text("cart_empty"), reply_markup=kb_cart_empty(), parse_mode="HTML"
        )
        await q.answer()
        return

    lines, total_qty, total_val = [], 0, 0.0
    for it in items:
        prod = await get_product(it.product_id)
        if not prod:
            continue
        price = effective_price(prod)
        sub = price * it.quantity
        lines.append(await get_text("cart_item_line",
                                    nome=prod.name, qtd=it.quantity,
                                    subtotal=fmt_brl(sub)))
        total_qty += it.quantity
        total_val += sub

    text = await get_text(
        "cart_header",
        lista="\n".join(lines), quantidade_total=total_qty,
        valor_total=fmt_brl(total_val), saldo=fmt_brl(user.balance),
    )
    await q.edit_message_text(text, reply_markup=kb_cart(), parse_mode="HTML")
    await q.answer()


async def show_remove_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    items = await get_cart(user.telegram_id)

    if not items:
        await q.answer("Carrinho vazio.", show_alert=True)
        return

    lista_items, lines = [], []
    for it in items:
        prod = await get_product(it.product_id)
        if not prod:
            continue
        lista_items.append({"cart_id": it.id, "product_name": prod.name})
        lines.append(f"• {prod.name} ({it.quantity}x)")

    text = await get_text("cart_remove_screen", lista="\n".join(lines))
    await q.edit_message_text(text, reply_markup=kb_cart_remove(lista_items),
                              parse_mode="HTML")
    await q.answer()


async def remove_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Produto excluído", show_alert=True)


async def remove_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    cart_id = int(q.data.split(":")[2])
    user = await get_or_create_user(update.effective_user)
    await remove_cart_item(cart_id, user.telegram_id)
    await q.answer("✓ Produto removido.")

    items = await get_cart(user.telegram_id)
    if not items:
        await q.edit_message_text(
            await get_text("cart_empty"), reply_markup=kb_cart_empty(), parse_mode="HTML"
        )
        return
    await show_remove_screen(update, context)


async def finalize_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    items = await get_cart(user.telegram_id)

    if not items:
        await q.answer("Carrinho vazio.", show_alert=True)
        return

    lines, total_qty, total_val, purchase_items = [], 0, 0.0, []
    for it in items:
        prod = await get_product(it.product_id)
        if not prod or not prod.active or not prod.visible:
            await q.answer("❌ Produto indisponível no carrinho.", show_alert=True)
            return
        stock = await count_stock(it.product_id)
        if stock < it.quantity:
            await q.answer(f"❌ Estoque insuficiente de {prod.name}.", show_alert=True)
            return
        price = effective_price(prod)
        sub = price * it.quantity
        lines.append(await get_text("cart_item_line",
                                    nome=prod.name, qtd=it.quantity,
                                    subtotal=fmt_brl(sub)))
        total_qty += it.quantity
        total_val += sub
        purchase_items.append({"product_id": it.product_id, "quantity": it.quantity})

    balance = float(user.balance)

    if balance < total_val:
        await q.edit_message_text(
            await get_text(
                "cart_insufficient_balance",
                total=fmt_brl(total_val), saldo=fmt_brl(balance),
                faltante=fmt_brl(round(total_val - balance, 2)),
            ),
            reply_markup=kb_qty_insufficient(), parse_mode="HTML",
        )
        await q.answer()
        return

    pending = {"type": "cart", "items": purchase_items,
               "total": total_val, "from_cart": True}
    await upsert_state(user.telegram_id,
                       pending_operation="purchase", pending_data=json.dumps(pending))

    await q.edit_message_text(
        await get_text(
            "cart_finalize_confirm",
            lista="\n".join(lines), quantidade_total=total_qty,
            valor_total=fmt_brl(total_val), saldo=fmt_brl(balance),
            saldo_final=fmt_brl(balance - total_val),
        ),
        reply_markup=kb_purchase_confirm(), parse_mode="HTML",
    )
    await q.answer()
