from telegram import Update
from telegram.ext import ContextTypes

from database import (
    count_products_by_category, get_category, get_or_create_user,
    list_categories, list_products_by_category,
)
from keyboards import kb_catalog_categories, kb_main_menu, kb_product_list
from texts import fmt_brl, get_text

PER_PAGE = 15


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = await get_or_create_user(update.effective_user)
    cats = await list_categories()

    if not cats:
        await q.edit_message_text(
            await get_text("catalog_empty"),
            reply_markup=kb_main_menu(), parse_mode="HTML",
        )
        await q.answer()
        return

    username = f"@{user.username}" if user.username else user.first_name
    text = await get_text(
        "catalog_header",
        username=username, user_id=user.telegram_id,
        saldo=fmt_brl(user.balance),
    )
    await q.edit_message_text(
        text, reply_markup=kb_catalog_categories(cats), parse_mode="HTML"
    )
    await q.answer()


async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, _, cat_id_s, page_s = q.data.split(":")
    cat_id, page = int(cat_id_s), int(page_s)

    cat = await get_category(cat_id)
    if not cat or not cat.active:
        await q.answer("Categoria indisponível.", show_alert=True)
        return

    total = await count_products_by_category(cat_id)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    products = await list_products_by_category(cat_id, PER_PAGE, page * PER_PAGE)

    if not products:
        await q.edit_message_text(
            await get_text("category_empty"),
            reply_markup=kb_product_list([], cat_id, 0, 1),
            parse_mode="HTML",
        )
        await q.answer()
        return

    text = f"📁 <b>{cat.name}</b>\n\nSelecione um produto:"
    await q.edit_message_text(
        text, reply_markup=kb_product_list(products, cat_id, page, total_pages),
        parse_mode="HTML",
    )
    await q.answer()
