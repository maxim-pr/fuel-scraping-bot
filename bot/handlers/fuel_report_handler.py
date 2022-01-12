import asyncio
import logging
import os
import uuid

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from parsers.departure_stations_parser import DepartureStationsParser
from parsers.errors import HtmlParsingError, ApiError, InvalidStationError, InvalidFuelError
from ..utils import save_as_xl


class FuelReportStates(StatesGroup):
    entering_fuel = State()
    entering_station = State()


class FuelReportHandler:
    def __init__(self):
        self._callback_data_factory = CallbackData('f', 'fuel_name')
        self._fuel_names = ('АИ-92-К5', 'АИ-95-К5',
                            'ДТ-А-К5', 'ДТ-Е-К5', 'ДТ-З-К5',
                            'ДТ-Л-К5', 'МАЗУТ', 'ТС-1')
        self._logger = logging.getLogger(__name__)

    def _create_fuel_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=3)

        for fuel_name in self._fuel_names:
            button = InlineKeyboardButton(
                text=fuel_name,
                callback_data=self._callback_data_factory.new(fuel_name=fuel_name)
            )
            keyboard.insert(button)

        return keyboard

    def fuel_step_filter(self):
        return self._callback_data_factory.filter()

    async def start_handler(self, message: types.Message, state: FSMContext):
        await message.answer('Выберите топливо:', reply_markup=self._create_fuel_keyboard())
        await state.set_state(FuelReportStates.entering_fuel)

        self._logger.info(f"{message.from_user.id}: /fuel_report")

    async def entered_fuel_handler(self, callback: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
        fuel_name = callback_data['fuel_name']
        await callback.answer(text=f"Вы выбрали {fuel_name}")
        await callback.message.edit_reply_markup()
        await callback.message.edit_text(f"Топливо: <b>{fuel_name}</b>")

        await state.update_data({'fuel_name': fuel_name})

        await callback.message.answer('Введите станцию прибытия:')
        await state.set_state(FuelReportStates.entering_station)

        self._logger.info(f"{callback.from_user.id}: {fuel_name}")

    async def entered_station_handler(self, message: types.Message, state: FSMContext):
        arrival_station = message.text
        fuel_name = (await state.get_data())['fuel_name']

        self._logger.info(f"{message.from_user.id}: {arrival_station}")

        parser = DepartureStationsParser()
        try:
            report = await parser.get_report(arrival_station, fuel_name)
        except asyncio.TimeoutError as err:
            self._logger.exception(err)
            await message.answer('spimex.com не отвечает(')
        except InvalidStationError as err:
            self._logger.exception(err)
            await message.answer(f"Во время обработки встретилась невалидная станция: {err.station}")
        except InvalidFuelError as err:
            self._logger.exception(err)
            await message.answer(f"{err.fuel} - невалидное топливо")
        except (ApiError, HtmlParsingError, aiohttp.ClientError) as err:
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
            await parser.close()
            await state.finish()


def register_fuel_report_handler(dp: Dispatcher, fuel_report_handler: FuelReportHandler):
    dp.register_message_handler(fuel_report_handler.start_handler,
                                commands=['fuel_report'])
    dp.register_callback_query_handler(fuel_report_handler.entered_fuel_handler,
                                       fuel_report_handler.fuel_step_filter(),
                                       state=FuelReportStates.entering_fuel)
    dp.register_message_handler(fuel_report_handler.entered_station_handler,
                                state=FuelReportStates.entering_station)
