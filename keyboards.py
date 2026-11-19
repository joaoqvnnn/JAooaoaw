from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import OFFICIAL_CHANNEL_LINK, OFFICIAL_GROUP_LINK
from texts import fmt_brl


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


def kb_catalog_categories(categories) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📁 {c.name}", callback_data=f"cat:open:{c.id}:0")]
            for c in categories]
    rows.append([InlineKeyboardButton("🏠 Menu principal", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def kb_product_list(products, cat_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        price = float(p.promo_price or p.price)
        label = f"{p.name} — R$ {fmt_brl(price)}"
        if len(label) > 60:
            label = label[:57] + "..."
        rows.append([InlineKeyboardButton(label, callback_data=f"prod:view:{p.id}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"cat:open:{cat_id}:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"cat:open:{cat_id}:{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Voltar", callback_data="catalog")])
    return InlineKeyboardMarkup(rows)


def kb_product_detail(prod_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar", callback_data=f"prod:buy:{prod_id}")],
        [InlineKeyboardButton("📦 Comprar quantidade", callback_data=f"prod:qty:{prod_id}")],
        [InlineKeyboardButton("➕ Adicionar ao carrinho", callback_data=f"prod:cart:{prod_id}")],
        [InlineKeyboardButton("💰 Adicionar saldo", callback_data="add_balance")],
        [InlineKeyboardButton("◀️ Voltar", callback_data="catalog")],
    ])


def kb_purchase_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirmar compra", callback_data="purchase:confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="purchase:cancel")],
    ])


def kb_qty_insufficient() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💠 Gerar PIX (Módulo 3)", callback_data="pix_pending")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="purchase:cancel")],
    ])


def kb_delivery(order_id: int, current_idx: int, total_items: int,
                show_creds: bool, activation_link: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    label = "🙈 Desativar visualização" if show_creds else "👁️ Ativar visualização"
    rows.append([InlineKeyboardButton(label, callback_data=f"deliv:toggle:{order_id}")])

    if total_items > 1:
        nav = []
        if current_idx > 0:
            nav.append(InlineKeyboardButton(
                "◀️", callback_data=f"deliv:page:{order_id}:{current_idx-1}"
            ))
        nav.append(InlineKeyboardButton(
            f"{current_idx+1}/{total_items}", callback_data="noop"
        ))
        if current_idx < total_items - 1:
            nav.append(InlineKeyboardButton(
                "➡️", callback_data=f"deliv:page:{order_id}:{current_idx+1}"
            ))
        rows.append(nav)

    if activation_link:
        rows.append([InlineKeyboardButton("🌐 Ativar produto", url=activation_link)])
    rows.append([InlineKeyboardButton("🏠 Menu principal", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def kb_cart() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Continuar comprando", callback_data="catalog")],
        [InlineKeyboardButton("🗑️ Remover produto", callback_data="cart:remove")],
        [InlineKeyboardButton("💰 Finalizar compra", callback_data="cart:finalize")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:main")],
    ])


def kb_cart_remove(items) -> InlineKeyboardMarkup:
    rows = []
    for it in items:
        name = it["product_name"]
        if len(name) > 18:
            name = name[:15] + "..."
        rows.append([
            InlineKeyboardButton(f"🗑️ {name}", callback_data=f"cart:delalert:{it['cart_id']}"),
            InlineKeyboardButton("✅ Confirmar", callback_data=f"cart:delconfirm:{it['cart_id']}"),
        ])
    rows.append([InlineKeyboardButton("◀️ Voltar ao carrinho", callback_data="cart")])
    return InlineKeyboardMarkup(rows)


def kb_cart_empty() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Continuar comprando", callback_data="catalog")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:main")],
    ])
