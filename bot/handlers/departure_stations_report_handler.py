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

from scrapers import DepartureStationsReporter
from scrapers.errors import HtmlParsingError, ApiResponseError, \
    InvalidStationError, InvalidFuelError
from ..utils import save_as_xl

logger = logging.getLogger(__name__)


class States(StatesGroup):
    entering_fuel = State()
    entering_station = State()


class DepartureStationsReportHandler:
    def __init__(self, scraper_config_file_path: str):
        self._scraper_config_file_path = scraper_config_file_path
        self._callback_data_factory = CallbackData('f', 'fuel_name')
        self._fuel_names = ('АИ-92-К5', 'АИ-95-К5',
                            'ДТ-А-К5', 'ДТ-Е-К5', 'ДТ-З-К5',
                            'ДТ-Л-К5', 'МАЗУТ', 'ТС-1')

    def _create_fuel_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=3)

        for fuel_name in self._fuel_names:
            button = InlineKeyboardButton(
                text=fuel_name,
                callback_data=self._callback_data_factory.new(
                    fuel_name=fuel_name
                )
            )
            keyboard.insert(button)

        return keyboard

    def fuel_step_filter(self):
        return self._callback_data_factory.filter()

    async def start_handler(self, message: types.Message, state: FSMContext):
        await message.answer('Выберите топливо:',
                             reply_markup=self._create_fuel_keyboard())
        await state.set_state(States.entering_fuel)

        logger.info(f'user={message.from_user.id} command={message.text}')

    async def entered_fuel_handler(self, callback: types.CallbackQuery,
                                   callback_data: dict[str, str],
                                   state: FSMContext):
        fuel_name = callback_data['fuel_name']
        logger.info(f'user={callback.from_user.id} callback_query={fuel_name}')

        await callback.answer(text=f"Вы выбрали {fuel_name}")
        await callback.message.edit_reply_markup()
        await callback.message.edit_text(f"Топливо: <b>{fuel_name}</b>")

        await state.update_data({'fuel_name': fuel_name})

        await callback.message.answer('Введите станцию прибытия:')
        await state.set_state(States.entering_station)

    async def entered_station_handler(self, message: types.Message,
                                      state: FSMContext):
        arrival_station = message.text
        logger.info(f'user={message.from_user.id} message={arrival_station}')

        fuel_name = (await state.get_data())['fuel_name']
        reporter = DepartureStationsReporter(self._scraper_config_file_path)
        try:
            report = await reporter.get_report(arrival_station, fuel_name)
        except asyncio.TimeoutError as err:
            logger.exception(err)
            await message.answer('сайт не отвечает(')
        except InvalidStationError as err:
            logger.exception(err)
            await message.answer(f'Во время обработки встретилась невалидная станция: {err.station}')
        except InvalidFuelError as err:
            logger.exception(err)
            await message.answer(f'{err.fuel} - невалидное топливо')
        except (ApiResponseError, HtmlParsingError, aiohttp.ClientResponseError) as err:
            logger.exception(err)
            await message.answer('Извините, что-то пошло не так(')
        except Exception as err:
            logger.exception(err)
            await message.answer('Извините, что-то совсем пошло не так(')
        else:
            file_name = uuid.uuid4()
            file_path = f"/tmp/{file_name}.xlsx"
            save_as_xl(report, file_path)
            with open(file_path, 'rb') as file:
                await message.answer_document(file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        finally:
            await reporter.close()
            await state.finish()

    def register(self, dp: Dispatcher):
        dp.register_message_handler(self.start_handler,
                                    commands=['departure_stations_report'])
        dp.register_callback_query_handler(self.entered_fuel_handler,
                                           self.fuel_step_filter(),
                                           state=States.entering_fuel)
        dp.register_message_handler(self.entered_station_handler,
                                    state=States.entering_station)
