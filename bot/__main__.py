import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from .config import setup_args_parser
from .handlers import DepartureStationsReportHandler, \
    DeliveryBasisReportHandler
from .logger import setup_logger

logger = logging.getLogger(__package__)


async def main():
    args_parser = setup_args_parser()
    args = args_parser.parse_args()

    setup_logger(logger)
    setup_logger(logging.getLogger('scrapers'))

    bot = Bot(args.bot_token, parse_mode='HTML')
    storage = RedisStorage2(host=args.redis_ip, port=args.redis_port,
                            password=args.redis_password, db=args.redis_db)
    dp = Dispatcher(bot, storage=storage)

    departure_stations_report_handler = DepartureStationsReportHandler(
        'data/scraper_config.yml'
    )
    departure_stations_report_handler.register(dp)

    delivery_basis_report_handler = DeliveryBasisReportHandler(
        'data/scraper_config.yml', 'data/delivery_basis_template.csv'
    )
    delivery_basis_report_handler.register(dp)

    logger.info('starting bot')
    try:
        await dp.start_polling()
    finally:
        logger.info('stopping bot')
        await dp.storage.close()
        await dp.storage.wait_closed()
        session = await dp.bot.get_session()
        await session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
