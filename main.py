import asyncio
import logging

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
)

import config
from database import init_db
from handlers_menu import cmd_cancelar, on_callback
from handlers_start import cmd_start, on_chat_member

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bellamy")


async def resolve_chat_ids(app: Application) -> None:
    """Converte @username → ID numérico para comparar com chat_member."""
    async def _resolve(ref: str) -> int | None:
        if not ref:
            return None
        try:
            if ref.lstrip("-").isdigit():
                return int(ref)
            chat = await app.bot.get_chat(ref)
            return chat.id
        except Exception as e:
            log.error("Falha resolvendo chat %s: %s", ref, e)
            return None

    config.CHANNEL_NUMERIC_ID = await _resolve(config.OFFICIAL_CHANNEL_ID)
    config.GROUP_NUMERIC_ID = await _resolve(config.OFFICIAL_GROUP_ID)
    log.info(
        "IDs resolvidos → canal=%s | grupo=%s",
        config.CHANNEL_NUMERIC_ID,
        config.GROUP_NUMERIC_ID,
    )


async def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN não configurado.")
    if not config.WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_URL não configurado.")

    await init_db()

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancelar", cmd_cancelar))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(
        ChatMemberHandler(on_chat_member, ChatMemberHandler.CHAT_MEMBER)
    )

    await app.initialize()
    await app.start()
    await resolve_chat_ids(app)

    webhook_path = "/webhook"
    webhook_url = f"{config.WEBHOOK_URL}{webhook_path}"
    await app.bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=False,
    )
    log.info("Webhook registrado em %s", webhook_url)

    async def webhook_handler(request: web.Request) -> web.Response:
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
        except Exception as e:
            log.exception("Erro processando update: %s", e)
        return web.Response(text="OK")

    async def health(request: web.Request) -> web.Response:
        return web.Response(text="BELLAMY BOT OK")

    aio_app = web.Application()
    aio_app.router.add_post(webhook_path, webhook_handler)
    aio_app.router.add_get("/", health)
    aio_app.router.add_get("/health", health)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()
    log.info("Servidor web ouvindo em 0.0.0.0:%s", config.PORT)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
