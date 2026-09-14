import asyncio
import logging
import uvicorn
from data import config
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError

from database.db import init_db
from middlewares import setup_middlewares
from app import handlers
from app.utils.notify_admins import notify_admins
from app.utils.set_bot_commands import set_bot_commands
from app.utils.misc.logging import setup_logger
from app.web.server import app as fastapi_app, set_bot

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def start_web_server():
    server_config = uvicorn.Config(
        app=fastapi_app,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level="info"
    )
    server = uvicorn.Server(server_config)
    await server.serve()

async def start_bot():
    try:
        await set_bot_commands(bot)
        await notify_admins(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except TelegramUnauthorizedError:
        logging.warning("⚠️ BOT_TOKEN yaroqsiz yoki test tokeni kiritilgan. Bot polling to'xtatildi, lekin Web App va Admin Panel serveri ishlashda davom etadi!")
    except Exception as e:
        logging.error(f"Bot polling xatosi: {e}")

async def main():
    setup_logger()
    logging.info("🚀 Stellar Bot va Web App serveri tayyorlanmoqda...")

    # Initialize Database
    await init_db()
    logging.info("✅ Ma'lumotlar bazasi initsializatsiya qilindi.")

    # Pass bot instance to web server
    set_bot(bot)

    # Setup middlewares and handlers
    setup_middlewares(dp)
    handlers.setup(dp)

    logging.info(f"🌐 Web App URL: {config.WEB_APP_URL}")
    logging.info(f"🌐 Admin Panel URL: {config.ADMIN_APP_URL}")

    # Concurrently run Web App and Telegram Bot polling
    await asyncio.gather(
        start_web_server(),
        start_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        try:
            asyncio.run(bot.session.close())
        except Exception:
            pass