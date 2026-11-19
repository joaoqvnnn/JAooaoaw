import re
from datetime import datetime

from config import BOT_NAME
from database import get_setting


DEFAULT_TEXTS = {
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
}


def get_greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "Bom dia"
    if 12 <= h < 18:
        return "Boa tarde"
    return "Boa noite"


def safe_format(template: str, **kwargs) -> str:
    """Substitui {chave} preservando chaves ausentes (evita KeyError)."""
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
