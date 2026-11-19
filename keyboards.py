from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import OFFICIAL_CHANNEL_LINK, OFFICIAL_GROUP_LINK


def kb_access_restricted() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Entrar no canal", url=OFFICIAL_CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Entrar no grupo", url=OFFICIAL_GROUP_LINK)],
    ])


def kb_main_menu(cart_count: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🎟️ Logins | Contas Premium", callback_data="catalog")],
        [InlineKeyboardButton("👤 Perfil", callback_data="profile")],
        [InlineKeyboardButton("💰 Adicionar saldo", callback_data="add_balance")],
        [InlineKeyboardButton("🏆 Ranking", callback_data="ranking")],
        [InlineKeyboardButton("💎 Indicação", callback_data="referral")],
        [InlineKeyboardButton("🆘 Atendimento", callback_data="support")],
    ]
    if cart_count > 0:
        rows.append([InlineKeyboardButton(f"🛒 Carrinho ({cart_count})", callback_data="cart")])
    return InlineKeyboardMarkup(rows)
