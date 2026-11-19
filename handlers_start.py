import logging

from telegram import ChatMember, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

import config
from database import get_or_create_user, get_state, upsert_state
from keyboards import kb_access_restricted, kb_main_menu
from texts import build_welcome, get_text

log = logging.getLogger(__name__)


def _is_in(member: ChatMember) -> bool:
    return member.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ) or getattr(member.status, "value", member.status) in ("creator", "member", "administrator")


async def is_user_in_chat(bot, chat_id: int, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return _is_in(m)
    except Exception as e:
        log.warning("Falha ao verificar membro %s em %s: %s", user_id, chat_id, e)
        return False


async def check_both(bot, user_id: int) -> bool:
    if not config.CHANNEL_NUMERIC_ID or not config.GROUP_NUMERIC_ID:
        return False
    in_channel = await is_user_in_chat(bot, config.CHANNEL_NUMERIC_ID, user_id)
    in_group = await is_user_in_chat(bot, config.GROUP_NUMERIC_ID, user_id)
    return in_channel and in_group


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if not tg_user:
        return

    user = await get_or_create_user(tg_user)

    if user.is_banned:
        await update.message.reply_text(
            "🚫 <b>Conta banida</b>\n\nSua conta está suspensa. "
            "Entre em contato com o suporte.",
            parse_mode="HTML",
        )
        return

    # Preserva deep link (usado em módulos futuros)
    if context.args:
        await upsert_state(tg_user.id, deep_link_arg=context.args[0][:128])

    if await check_both(context.bot, tg_user.id):
        text = build_welcome(user)
        msg = await update.message.reply_text(
            text, reply_markup=kb_main_menu(), parse_mode="HTML"
        )
        await upsert_state(
            tg_user.id, screen="menu", message_id=msg.message_id, chat_id=msg.chat_id
        )
        return

    text = await get_text("access_restricted")
    msg = await update.message.reply_text(
        text, reply_markup=kb_access_restricted(), parse_mode="HTML"
    )
    await upsert_state(
        tg_user.id, screen="restricted", message_id=msg.message_id, chat_id=msg.chat_id
    )


async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = update.chat_member
    if not cm:
        return

    chat_id = cm.chat.id
    if chat_id not in (config.CHANNEL_NUMERIC_ID, config.GROUP_NUMERIC_ID):
        return

    new_member = cm.new_chat_member
    tg_user = new_member.user
    if tg_user.is_bot:
        return

    # Só dispara quando o usuário ENTRA (não quando sai)
    from telegram.constants import ChatMemberStatus as S
    entrou = new_member.status in (S.MEMBER, S.ADMINISTRATOR, S.OWNER)
    if not entrou:
        return

    if not await check_both(context.bot, tg_user.id):
        return

    state = await get_state(tg_user.id)
    if state and state.screen == "menu":
        return  # acesso já liberado — idempotência

    user = await get_or_create_user(tg_user)
    welcome = build_welcome(user)

    if state and state.message_id and state.chat_id:
        try:
            await context.bot.edit_message_text(
                chat_id=state.chat_id,
                message_id=state.message_id,
                text=welcome,
                reply_markup=kb_main_menu(),
                parse_mode="HTML",
            )
            await upsert_state(tg_user.id, screen="menu")
            return
        except Exception as e:
            log.warning("Não editou mensagem de bloqueio: %s", e)

    # Fallback: envia novo welcome (caso bot tenha perdido a mensagem anterior)
    try:
        msg = await context.bot.send_message(
            chat_id=tg_user.id,
            text=welcome,
            reply_markup=kb_main_menu(),
            parse_mode="HTML",
        )
        await upsert_state(
            tg_user.id, screen="menu", message_id=msg.message_id, chat_id=msg.chat_id
        )
    except Exception as e:
        log.warning("Falha ao enviar welcome para %s: %s", tg_user.id, e)
