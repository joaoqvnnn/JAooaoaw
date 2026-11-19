import re
from datetime import datetime

from config import BOT_NAME
from database import get_setting


DEFAULT_TEXTS = {
    # -------- módulo 1 --------
    "access_restricted": (
        "🔒 <b>ACESSO RESTRITO</b>\n\n"
        "Para utilizar nossos serviços, é necessário participar dos nossos "
        "espaços oficiais no Telegram.\n\n"
        "Entre nos dois espaços abaixo para liberar seu acesso:\n\n"
        "👇 Escolha os espaços para entrar:"
    ),
    "welcome": (
        "🌤️ {saudacao}, {nome_bot}\n\n"
        "🐼 Seja muito bem-vindo(a) à nossa loja!\n\n"
        "Descubra uma maneira simples e prática de realizar suas compras "
        "diretamente pelo Telegram.\n\n"
        "👨‍💻 Sistema automatizado para facilitar seus pedidos.\n\n"
        "💠 Recargas de saldo de forma rápida.\n\n"
        "🛒 Produtos e serviços disponíveis em nosso catálogo.\n\n"
        "Navegue pelo menu e encontre o que procura em poucos cliques!\n\n"
        "❗️ <b>INFORMAÇÕES IMPORTANTES</b>\n\n"
        "Antes de adicionar saldo, confira a disponibilidade dos produtos desejados.\n\n"
        "Não realizamos reembolsos em dinheiro. Eventuais problemas serão tratados "
        "conforme nossa política de atendimento, com a devida análise.\n\n"
        "👇 Comece agora e aproveite nossos serviços!\n\n"
        "ℹ️ <b>SEU PERFIL</b>\n\n"
        "➩ Usuário: {username}\n"
        "➩ ID: {user_id}\n"
        "➩ Saldo: R$ {saldo}"
    ),
    "cancel_operation": (
        "❌ <b>OPERAÇÃO CANCELADA!</b>\n\n"
        "A operação foi encerrada com sucesso.\n\n"
        "Você poderá iniciar uma nova operação quando desejar."
    ),

    # -------- módulo 2 — catálogo --------
    "catalog_header": (
        "🎟️ <b>𝗖𝗔𝗧𝗔𝗟𝗢𝗚𝗢 𝗗𝗘 𝗔𝗖𝗘𝗦𝗦𝗢𝗦</b>\n\n"
        "◆ ━━━━━━━━❪✪❫━━━━━━━━ ◆\n\n"
        "👤 | Conta: {username}\n"
        "🆔 | Identificação: {user_id}\n"
        "💰 | Seu saldo: R$ {saldo}\n\n"
        "◆ ━━━━━━━━❪✪❫━━━━━━━━ ◆\n\n"
        "<b>𝗟𝗢𝗚𝗜𝗡𝗦 • 𝗖𝗢𝗡𝗧𝗔𝗦 • 𝗧𝗘𝗟𝗔𝗦</b>\n\n"
        "◆ ━━━━━━━━❪✪❫━━━━━━━━ ◆\n\n"
        "👇 Selecione uma das opções disponíveis para continuar:"
    ),
    "catalog_empty": (
        "😕 <b>Nenhuma categoria disponível</b>\n\n"
        "Volte mais tarde!"
    ),
    "category_empty": "😕 Nenhum produto disponível nesta categoria no momento.",

    # -------- detalhe do produto --------
    "product_detail": (
        "🛍️ <b>CONFIRA OS DETALHES DO PRODUTO</b>\n\n"
        "🔹 | Serviço: {nome_produto}\n\n"
        "✨ | Preço: R$ {preco}\n\n"
        "💳 | Saldo disponível: R$ {saldo}\n\n"
        "📦 | Estoque disponível: {estoque}\n\n"
        "🔎 <b>INFORMAÇÕES DO PRODUTO:</b>\n\n"
        "{descricao}\n\n"
        "👀 {visualizacoes} pessoas visualizando este serviço."
    ),

    # -------- confirmação / cancelamento / sucesso --------
    "purchase_confirm": (
        "🛍️ <b>CONFIRME SEU PEDIDO</b>\n\n"
        "📦 Produto: {produto}\n\n"
        "🔢 Quantidade: {quantidade}\n\n"
        "💰 Valor total: R$ {total}\n\n"
        "💳 Saldo atual: R$ {saldo}\n\n"
        "💸 Saldo após compra: R$ {saldo_final}\n\n"
        "Deseja confirmar esta compra?"
    ),
    "purchase_cancelled": (
        "❌ <b>COMPRA CANCELADA!</b>\n\n"
        "Sua compra foi cancelada com sucesso.\n\n"
        "Nenhum valor foi descontado da sua carteira."
    ),

    # -------- compra por quantidade --------
    "qty_prompt": (
        "📦 <b>QUANTOS LOGINS DESEJA COMPRAR?</b>\n\n"
        "📊 Estoque disponível: {estoque}\n\n"
        "💡 Digite a quantidade desejada.\n\n"
        "Para cancelar a operação, digite /cancelar."
    ),
    "qty_invalid": "⚠️ Valor inválido.\n\nDigite apenas números (ex.: 1, 2, 3).",
    "qty_below_min": "⚠️ Quantidade abaixo do mínimo permitido: {min}",
    "qty_above_max": "⚠️ Quantidade acima do máximo permitido: {max}",
    "qty_above_stock": "⚠️ Estoque insuficiente. Disponíveis: {available}",
    "qty_insufficient_balance": (
        "❌ <b>SALDO INSUFICIENTE!</b>\n\n"
        "🛍️ Produto: {produto}\n\n"
        "📦 Quantidade: {quantidade}\n\n"
        "💰 Seu saldo: R$ {saldo}\n\n"
        "💵 Valor total: R$ {total}\n\n"
        "📉 Faltam: R$ {faltante}\n\n"
        "Deseja gerar um PIX para completar sua compra?"
    ),

    # -------- entrega --------
    "delivery_hidden": (
        "📦 Item {atual}/{total} — {produto}\n\n"
        "📧 E-mail: {email_masked}\n"
        "🔑 Senha: {senha_masked}"
    ),
    "delivery_visible": (
        "📦 Item {atual}/{total} — {produto}\n\n"
        "📧 E-mail: <code>{email}</code>\n"
        "🔑 Senha: <code>{senha}</code>"
    ),

    # -------- carrinho --------
    "cart_empty": (
        "🛒 <b>Seu carrinho está vazio</b>\n\n"
        "Adicione produtos para começar!"
    ),
    "cart_header": (
        "🛒 <b>MEU CARRINHO</b>\n\n"
        "Confira seus produtos antes de finalizar.\n\n"
        "{lista}\n\n"
        "📦 Total de unidades: {quantidade_total}\n\n"
        "💰 Valor total: R$ {valor_total}\n\n"
        "💳 Seu saldo: R$ {saldo}"
    ),
    "cart_item_line": "• {nome} — {qtd}x — R$ {subtotal}",
    "cart_remove_screen": (
        "🗑️ <b>REMOVER PRODUTO</b>\n\n"
        "{lista}\n\n"
        "Selecione o produto que deseja remover:"
    ),
    "cart_finalize_confirm": (
        "🛍️ <b>CONFIRME SUA COMPRA</b>\n\n"
        "{lista}\n\n"
        "📦 Total de unidades: {quantidade_total}\n\n"
        "💰 Valor total: R$ {valor_total}\n\n"
        "💳 Saldo atual: R$ {saldo}\n\n"
        "💸 Saldo após compra: R$ {saldo_final}\n\n"
        "Deseja confirmar esta compra?"
    ),
    "cart_insufficient_balance": (
        "❌ <b>SALDO INSUFICIENTE!</b>\n\n"
        "💰 Valor total: R$ {total}\n\n"
        "💳 Seu saldo: R$ {saldo}\n\n"
        "📉 Faltam: R$ {faltante}\n\n"
        "Deseja gerar um PIX para completar sua compra?"
    ),
}


def get_greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "Bom dia"
    if 12 <= h < 18:
        return "Boa tarde"
    return "Boa noite"


def safe_format(template: str, **kwargs) -> str:
    def repl(m):
        key = m.group(1)
        return str(kwargs.get(key, m.group(0)))
    return re.sub(r"\{(\w+)\}", repl, template)


async def get_text(key: str, **kwargs) -> str:
    raw = await get_setting(f"text_{key}")
    if not raw:
        raw = DEFAULT_TEXTS.get(key, "")
    return safe_format(raw, **kwargs) if kwargs else raw


def fmt_brl(value) -> str:
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except Exception:
        return "0,00"


def build_welcome(user) -> str:
    username = f"@{user.username}" if user.username else user.first_name
    return safe_format(
        DEFAULT_TEXTS["welcome"],
        saudacao=get_greeting(),
        nome_bot=BOT_NAME,
        username=username,
        user_id=user.telegram_id,
        saldo=fmt_brl(user.balance),
    )
