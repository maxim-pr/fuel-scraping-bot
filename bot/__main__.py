import asyncio

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from .config import load_config
from .handlers.fuel_report_handler import FuelReportHandler, register_fuel_report_handler
from .logger import setup_logger


async def main():
    config = load_config()

    logger = setup_logger()

    bot = Bot(config.BOT_TOKEN, parse_mode='HTML')
    storage = RedisStorage2(host=config.REDIS_IP, port=config.REDIS_PORT, db=config.REDIS_DB)
    dp = Dispatcher(bot, storage=storage)

    fuel_report_handler = FuelReportHandler()
    register_fuel_report_handler(dp, fuel_report_handler)

    logger.info('starting bot')
    try:
        await dp.start_polling()
    finally:
        logger.info('stopping bot')
        await dp.storage.close()
        await dp.storage.wait_closed()
        await dp.bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
