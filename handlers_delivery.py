from telegram import Update
from telegram.ext import ContextTypes

from database import get_order_with_credentials, get_product
from keyboards import kb_delivery
from texts import get_text


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "••••••"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = "•" * len(local)
    else:
        masked = local[0] + "•" * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"


def _mask_password(pwd: str) -> str:
    return "•" * min(12, max(6, len(pwd or "")))


async def _load_deliveries(order_id: int, user_tg_id: int):
    data = await get_order_with_credentials(order_id, user_tg_id)
    if not data:
        return None
    deliveries = []
    for entry in data["items"]:
        item = entry["item"]
        prod = await get_product(item.product_id)
        for cred in entry["credentials"]:
            deliveries.append({
                "product": item.product_name,
                "email": cred["email"],
                "password": cred["password"],
                "activation_link": prod.activation_link if prod else None,
            })
    return deliveries


async def show_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    user_tg_id = update.effective_user.id
    deliveries = await _load_deliveries(order_id, user_tg_id)

    if not deliveries:
        msg = "❌ Nenhuma credencial encontrada para este pedido."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
            await update.callback_query.answer()
        else:
            await update.message.reply_text(msg)
        return

    context.user_data[f"deliv_page_{order_id}"] = 0
    context.user_data[f"deliv_visible_{order_id}"] = False
    await _render(update, context, order_id, deliveries, 0, False)


async def _render(update, context, order_id, deliveries, idx, visible):
    current = deliveries[idx]
    total = len(deliveries)

    if visible:
        body = await get_text(
            "delivery_visible",
            atual=idx + 1, total=total, produto=current["product"],
            email=current["email"], senha=current["password"],
        )
    else:
        body = await get_text(
            "delivery_hidden",
            atual=idx + 1, total=total, produto=current["product"],
            email_masked=_mask_email(current["email"]),
            senha_masked=_mask_password(current["password"]),
        )

    header = (
        "✅ <b>COMPRA REALIZADA COM SUCESSO!</b>\n\n"
        f"🆔 Pedido: #{order_id}\n\n"
        "◆ ━━━━━━━━❪✪❫━━━━━━━━ ◆\n\n"
    )
    full = header + body
    kb = kb_delivery(order_id, idx, total, visible, current.get("activation_link"))

    if update.callback_query:
        await update.callback_query.edit_message_text(full, reply_markup=kb, parse_mode="HTML")
    else:
        await update.message.reply_text(full, reply_markup=kb, parse_mode="HTML")


async def toggle_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    order_id = int(q.data.split(":")[2])
    visible = not context.user_data.get(f"deliv_visible_{order_id}", False)
    context.user_data[f"deliv_visible_{order_id}"] = visible
    idx = context.user_data.get(f"deliv_page_{order_id}", 0)

    deliveries = await _load_deliveries(order_id, update.effective_user.id)
    if not deliveries:
        await q.answer("❌ Pedido não encontrado.", show_alert=True)
        return

    await _render(update, context, order_id, deliveries, idx, visible)
    await q.answer()


async def page_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, _, order_id_s, idx_s = q.data.split(":")
    order_id, idx = int(order_id_s), int(idx_s)
    visible = context.user_data.get(f"deliv_visible_{order_id}", False)
    context.user_data[f"deliv_page_{order_id}"] = idx

    deliveries = await _load_deliveries(order_id, update.effective_user.id)
    if not deliveries:
        await q.answer("❌ Pedido não encontrado.", show_alert=True)
        return

    await _render(update, context, order_id, deliveries, idx, visible)
    await q.answer()
