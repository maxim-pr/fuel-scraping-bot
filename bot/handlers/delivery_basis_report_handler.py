import asyncio
import logging
import os
import uuid

import aiohttp
from aiogram import Dispatcher
from aiogram import types

from scrapers import DeliveryBasisReporter
from scrapers.errors import ApiResponseError, HtmlParsingError
from ..utils import save_as_xl

logger = logging.getLogger(__name__)


class DeliveryBasisReportHandler:
    def __init__(self, scraper_config_file_path: str, template_file_path: str):
        self._scraper_config_file_path = scraper_config_file_path
        self._template_file_path = template_file_path

    async def handler(self, message: types.Message):
        logger.info(f'user={message.from_user.id} command={message.text}')

        reporter = DeliveryBasisReporter(
            self._template_file_path, self._scraper_config_file_path
        )
        try:
            report = await reporter.get_report()
        except asyncio.TimeoutError as err:
            logger.exception(err)
            await message.answer('сайт не отвечает(')
        except (ApiResponseError, HtmlParsingError, aiohttp.ClientResponseError) as err:
            logger.exception(err)
            await message.answer('Извините, что-то пошло не так(')
        except Exception as err:
            logger.exception(err)
            await message.answer('Извините, что-то совсем пошло не так(')
        else:
            file_name = uuid.uuid4()
            file_path = f'/tmp/{file_name}.xlsx'
            save_as_xl(report, file_path)
            with open(file_path, 'rb') as file:
                await message.answer_document(file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        finally:
            await reporter.close()

    def register(self, dp: Dispatcher):
        dp.register_message_handler(self.handler,
                                    commands=['delivery_basis_report'])
