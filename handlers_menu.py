from telegram import Update
from telegram.ext import ContextTypes

from database import get_or_create_user, cart_total_qty, upsert_state
from keyboards import kb_main_menu
from texts import build_welcome, get_text


PLACEHOLDERS = {
    "profile": "🛠️ Perfil — Módulo 4",
    "add_balance": "🛠️ Adicionar saldo — Módulo 3",
    "ranking": "🛠️ Ranking — Módulo 6",
    "referral": "🛠️ Indicação — Módulo 5",
    "support": "🛠️ Atendimento — Módulo 7",
    "pix_pending": "🛠️ PIX — Módulo 3",
}


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    cart_count = await cart_total_qty(user.telegram_id)
    text = build_welcome(user)
    await q.edit_message_text(text, reply_markup=kb_main_menu(cart_count), parse_mode="HTML")
    await q.answer()


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q:
        return
    data = q.data or ""

    if data == "noop":
        await q.answer()
        return

    if data == "menu:main":
        await return_to_menu(update, context)
        return

    if data == "catalog":
        from handlers_catalog import show_catalog
        await show_catalog(update, context)
        return

    if data.startswith("cat:open:"):
        from handlers_catalog import show_category
        await show_category(update, context)
        return

    if data.startswith("prod:view:"):
        from handlers_product import show_product
        await show_product(update, context)
        return

    if data.startswith("prod:buy:"):
        from handlers_product import buy_individual
        await buy_individual(update, context)
        return

    if data.startswith("prod:qty:"):
        from handlers_product import ask_quantity
        await ask_quantity(update, context)
        return

    if data.startswith("prod:cart:"):
        from handlers_cart import add_product_to_cart
        await add_product_to_cart(update, context)
        return

    if data == "purchase:confirm":
        from handlers_product import confirm_purchase
        await confirm_purchase(update, context)
        return

    if data == "purchase:cancel":
        from handlers_product import cancel_purchase
        await cancel_purchase(update, context)
        return

    if data.startswith("deliv:toggle:"):
        from handlers_delivery import toggle_visibility
        await toggle_visibility(update, context)
        return

    if data.startswith("deliv:page:"):
        from handlers_delivery import page_delivery
        await page_delivery(update, context)
        return

    if data in ("cart", "cart:view"):
        from handlers_cart import show_cart
        await show_cart(update, context)
        return

    if data == "cart:remove":
        from handlers_cart import show_remove_screen
        await show_remove_screen(update, context)
        return

    if data.startswith("cart:delalert:"):
        from handlers_cart import remove_alert
        await remove_alert(update, context)
        return

    if data.startswith("cart:delconfirm:"):
        from handlers_cart import remove_confirm
        await remove_confirm(update, context)
        return

    if data == "cart:finalize":
        from handlers_cart import finalize_cart
        await finalize_cart(update, context)
        return

    if data in PLACEHOLDERS:
        await q.answer(PLACEHOLDERS[data], show_alert=True)
        return

    await q.answer("Ação não reconhecida.", show_alert=True)


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if not tg_user:
        return
    context.user_data.pop("awaiting", None)
    await upsert_state(tg_user.id, pending_operation=None, pending_data=None)
    text = await get_text("cancel_operation")
    await update.message.reply_text(text, parse_mode="HTML")
