import asyncio

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from .config import setup_args_parser
from .handlers.fuel_report_handler import FuelReportHandler, register_fuel_report_handler
from .handlers.delivery_basis_report_handler import DeliveryBasisReportHandler, register_delivery_basis_report_handler
from .logger import setup_logger


async def main():
    args_parser = setup_args_parser()
    args = args_parser.parse_args()

    logger = setup_logger()

    bot = Bot(args.bot_token, parse_mode='HTML')
    storage = RedisStorage2(host=args.redis_ip, port=args.redis_port,
                            password=args.redis_password, db=args.redis_db)
    dp = Dispatcher(bot, storage=storage)

    fuel_report_handler = FuelReportHandler()
    register_fuel_report_handler(dp, fuel_report_handler)

    delivery_basis_report_handler = DeliveryBasisReportHandler()
    register_delivery_basis_report_handler(dp, delivery_basis_report_handler)

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
