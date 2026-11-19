import json

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    add_to_cart, cart_total_qty, clear_cart, count_stock, count_viewers,
    execute_purchase, get_or_create_user, get_product, get_state,
    register_view, upsert_state,
)
from keyboards import (
    kb_main_menu, kb_product_detail, kb_purchase_confirm, kb_qty_insufficient,
)
from texts import fmt_brl, get_text


def effective_price(p) -> float:
    if p.promo_price is not None and float(p.promo_price) > 0:
        return float(p.promo_price)
    return float(p.price)


async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    prod_id = int(q.data.split(":")[2])
    user = await get_or_create_user(update.effective_user)
    prod = await get_product(prod_id)

    if not prod or not prod.active or not prod.visible:
        await q.answer("❌ Produto indisponível.", show_alert=True)
        return

    await register_view(user.telegram_id, prod_id)
    viewers = await count_viewers(prod_id)
    stock = await count_stock(prod_id)
    price = effective_price(prod)

    text = await get_text(
        "product_detail",
        nome_produto=prod.name, preco=fmt_brl(price),
        saldo=fmt_brl(user.balance), estoque=stock,
        descricao=prod.description or "—", visualizacoes=viewers,
    )
    try:
        await q.edit_message_text(
            text, reply_markup=kb_product_detail(prod_id), parse_mode="HTML"
        )
    except Exception:
        await q.message.reply_text(
            text, reply_markup=kb_product_detail(prod_id), parse_mode="HTML"
        )
    await q.answer()


async def buy_individual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    prod_id = int(q.data.split(":")[2])
    user = await get_or_create_user(update.effective_user)
    prod = await get_product(prod_id)

    if not prod or not prod.active or not prod.visible:
        await q.answer("❌ Produto indisponível.", show_alert=True)
        return

    stock = await count_stock(prod_id)
    if stock < 1:
        await q.answer("❌ Produto esgotado.", show_alert=True)
        return

    price = effective_price(prod)
    balance = float(user.balance)

    if balance < price:
        faltante = round(price - balance, 2)
        await q.answer(
            f"❌ SALDO INSUFICIENTE!\n\n"
            f"🛍️ Produto: {prod.name}\n\n"
            f"💰 Valor do produto: R$ {fmt_brl(price)}\n\n"
            f"💳 Seu saldo: R$ {fmt_brl(balance)}\n\n"
            f"📉 Valor que falta: R$ {fmt_brl(faltante)}\n\n"
            f"Adicione saldo para concluir sua compra.",
            show_alert=True,
        )
        return

    pending = {"type": "individual",
               "items": [{"product_id": prod_id, "quantity": 1}],
               "total": price}
    await upsert_state(user.telegram_id,
                       pending_operation="purchase",
                       pending_data=json.dumps(pending))

    text = await get_text(
        "purchase_confirm",
        produto=prod.name, quantidade=1,
        total=fmt_brl(price), saldo=fmt_brl(balance),
        saldo_final=fmt_brl(balance - price),
    )
    await q.edit_message_text(text, reply_markup=kb_purchase_confirm(), parse_mode="HTML")
    await q.answer()


async def ask_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    prod_id = int(q.data.split(":")[2])
    prod = await get_product(prod_id)

    if not prod:
        await q.answer("❌ Produto indisponível.", show_alert=True)
        return

    stock = await count_stock(prod_id)
    if stock < prod.min_qty:
        await q.answer(f"❌ Estoque insuficiente. Mínimo: {prod.min_qty}",
                       show_alert=True)
        return

    context.user_data["awaiting"] = {"type": "quantity", "product_id": prod_id}
    await q.message.reply_text(
        await get_text("qty_prompt", estoque=stock), parse_mode="HTML"
    )
    await q.answer()


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    awaiting = context.user_data.get("awaiting")
    if not awaiting or awaiting.get("type") != "quantity":
        return False

    text = (update.message.text or "").strip()
    if not text.isdigit():
        await update.message.reply_text(await get_text("qty_invalid"), parse_mode="HTML")
        return True

    qty = int(text)
    prod_id = awaiting["product_id"]
    prod = await get_product(prod_id)
    if not prod:
        await update.message.reply_text("❌ Produto indisponível.")
        context.user_data.pop("awaiting", None)
        return True

    stock = await count_stock(prod_id)

    if qty < prod.min_qty:
        await update.message.reply_text(
            await get_text("qty_below_min", min=prod.min_qty), parse_mode="HTML"
        )
        return True
    if qty > prod.max_qty:
        await update.message.reply_text(
            await get_text("qty_above_max", max=prod.max_qty), parse_mode="HTML"
        )
        return True
    if qty > stock:
        await update.message.reply_text(
            await get_text("qty_above_stock", available=stock), parse_mode="HTML"
        )
        return True

    context.user_data.pop("awaiting", None)
    user = await get_or_create_user(update.effective_user)
    price = effective_price(prod)
    total = price * qty
    balance = float(user.balance)

    if balance < total:
        faltante = round(total - balance, 2)
        await update.message.reply_text(
            await get_text(
                "qty_insufficient_balance",
                produto=prod.name, quantidade=qty,
                saldo=fmt_brl(balance), total=fmt_brl(total),
                faltante=fmt_brl(faltante),
            ),
            reply_markup=kb_qty_insufficient(), parse_mode="HTML",
        )
        return True

    pending = {"type": "quantity",
               "items": [{"product_id": prod_id, "quantity": qty}],
               "total": total}
    await upsert_state(user.telegram_id,
                       pending_operation="purchase",
                       pending_data=json.dumps(pending))

    await update.message.reply_text(
        await get_text(
            "purchase_confirm",
            produto=prod.name, quantidade=qty,
            total=fmt_brl(total), saldo=fmt_brl(balance),
            saldo_final=fmt_brl(balance - total),
        ),
        reply_markup=kb_purchase_confirm(), parse_mode="HTML",
    )
    return True


async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    state = await get_state(user.telegram_id)

    if not state or state.pending_operation != "purchase" or not state.pending_data:
        await q.answer("❌ Nenhuma compra pendente.", show_alert=True)
        return

    pending = json.loads(state.pending_data)
    items = pending.get("items", [])
    result = await execute_purchase(user.telegram_id, items)

    if not result["ok"]:
        err = result.get("error")
        await upsert_state(user.telegram_id, pending_operation=None, pending_data=None)
        if err == "saldo":
            await q.answer(
                f"❌ Saldo insuficiente.\n\nFaltam: R$ {fmt_brl(result['faltante'])}",
                show_alert=True,
            )
        elif err == "estoque":
            await q.answer(f"❌ Estoque insuficiente para {result['product']}.",
                           show_alert=True)
        else:
            await q.answer("❌ Erro ao processar compra.", show_alert=True)
        return

    await upsert_state(user.telegram_id, pending_operation=None, pending_data=None)
    if pending.get("from_cart"):
        await clear_cart(user.telegram_id)

    await q.answer("✅ Compra realizada!")
    from handlers_delivery import show_delivery
    await show_delivery(update, context, result["order_id"])


async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    await upsert_state(user.telegram_id, pending_operation=None, pending_data=None)
    cart_count = await cart_total_qty(user.telegram_id)
    await q.edit_message_text(
        await get_text("purchase_cancelled"),
        reply_markup=kb_main_menu(cart_count), parse_mode="HTML",
    )
    await q.answer()
