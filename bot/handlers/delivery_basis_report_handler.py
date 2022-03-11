import asyncio
import logging
import os
import uuid

import aiohttp
from aiogram import Dispatcher
from aiogram import types

from parsers.delivery_basis_report.delivery_basis_report import \
    DeliveryBasisReporter
from parsers.errors import ApiResponseError, HtmlParsingError
from ..utils import save_as_xl


class DeliveryBasisReportHandler:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    async def handler(self, message: types.Message):
        self._logger.info(f"{message.from_user.id}: {message.text}")

        reporter = DeliveryBasisReporter(
            template_file_path='parsers/delivery_basis_report/template.csv'
        )
        try:
            report = await reporter.get_report()
        except asyncio.TimeoutError as err:
            self._logger.exception(err)
            await message.answer('spimex.com не отвечает(')
        except (ApiResponseError, HtmlParsingError, aiohttp.ClientError) as err:
            self._logger.exception(err)
            await message.answer('Извините, что-то пошло не так(')
        except Exception as err:
            self._logger.exception(err)
            await message.answer('Извините, что-то совсем пошло не так(')
        else:
            file_name = uuid.uuid4()
            file_path = f"/tmp/{file_name}.xlsx"
            save_as_xl(report, file_path)
            await message.answer_document(open(file_path, 'rb'))
            if os.path.isfile(file_path):
                os.remove(file_path)
        finally:
            await reporter.close()


def register_delivery_basis_report_handler(
        dp: Dispatcher,
        delivery_basis_report_handler: DeliveryBasisReportHandler
):
    dp.register_message_handler(
        delivery_basis_report_handler.handler,
        commands=['delivery_basis_report']
    )
