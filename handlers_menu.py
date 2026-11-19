from telegram import Update
from telegram.ext import ContextTypes

from database import upsert_state
from texts import get_text

PLACEHOLDERS = {
    "catalog": "🛠️ Catálogo — Módulo 2",
    "profile": "🛠️ Perfil — Módulo 4",
    "add_balance": "🛠️ Adicionar saldo — Módulo 3",
    "ranking": "🛠️ Ranking — Módulo 6",
    "referral": "🛠️ Indicação — Módulo 5",
    "support": "🛠️ Atendimento — Módulo 7",
    "cart": "🛠️ Carrinho — Módulo 3",
}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q:
        return
    data = q.data or ""

    if data in PLACEHOLDERS:
        await q.answer(PLACEHOLDERS[data], show_alert=True)
        return

    await q.answer("Ação não reconhecida.", show_alert=True)


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if not tg_user:
        return
    await upsert_state(tg_user.id, pending_operation=None, pending_data=None)
    text = await get_text("cancel_operation")
    await update.message.reply_text(text, parse_mode="HTML")
