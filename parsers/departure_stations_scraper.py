import numpy as np
import pandas as pd

from .calculator_scraper import CalculatorScraper
from .config.loader import load_config
from .trade_results_scraper import TradeResultsScraper


class DepartureStationsScraper:
    def __init__(self):
        config = load_config()
        self._FUEL_NAME_TO_INSTRUMENT_CODES = \
            config['FUEL_NAME_TO_INSTRUMENT_CODES']
        self._FUEL_NAME_TO_CALCULATOR_ITEM = \
            config['FUEL_NAME_TO_CALCULATOR_ITEM']
        self._CALCULATOR_ITEM_WEIGHTS = config['CALCULATOR_ITEM_WEIGHTS']
        self._DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME = \
            config['DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME']

        self._trade_results_parser = TradeResultsScraper()
        self._calculator_parser = CalculatorScraper(
            config['CALCULATOR_URL'], config['API_ENDPOINT_URL']
        )

    async def get_report(self, calculator_arrival_station: str,
                         fuel_name: str) -> pd.DataFrame:
        """

        :param calculator_arrival_station: name of arrival station
        AS IN CALCULATOR
        :param fuel_name:
        :return:
        """

        if fuel_name not in self._FUEL_NAME_TO_INSTRUMENT_CODES.keys():
            raise ValueError(
                f"fuel_name should be one of "
                f"{tuple(self._FUEL_NAME_TO_INSTRUMENT_CODES.keys())}"
            )

        # map fuel name to corresponding codes
        instrument_code_prefixes = self._FUEL_NAME_TO_INSTRUMENT_CODES.get(
            fuel_name)

        # map received fuel name to calculator fuel name
        calculator_fuel_name = self._FUEL_NAME_TO_CALCULATOR_ITEM.get(
            fuel_name)
        calculator_fuel_weight = self._CALCULATOR_ITEM_WEIGHTS[
            calculator_fuel_name]

        # retrieve all the possible instruments
        all_instruments = await self._trade_results_parser.retrieve_all_instruments()

        # filter all instruments by instrument code prefixes
        instruments: pd.DataFrame = \
            all_instruments.loc[all_instruments['Код Инструмента'].str.
                                    startswith(instrument_code_prefixes), :]

        # add columns
        instruments.loc[:, 'Название станции (как в калькуляторе)'] = np.NaN
        instruments.loc[:, 'Название топлива (как в калькуляторе)'] = calculator_fuel_name
        instruments.loc[:, 'Вес топлива (проставляемый в калькуляторе)'] = calculator_fuel_weight
        instruments.loc[:, 'РЖД стоимость'] = np.NaN
        instruments.loc[:, 'РЖД стоимость + 10%'] = np.NaN
        instruments.loc[:, 'Общая стоимость'] = np.NaN

        # iterate through all the instruments
        for i in instruments.index:

            # 1) map delivery basis to calculator fuel name
            delivery_basis = instruments.loc[i, 'Базис поставки']
            if self._DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME.get(delivery_basis):
                calculator_departure_station = \
                    self._DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME[delivery_basis]
            elif delivery_basis.startswith('ст. '):
                calculator_departure_station = delivery_basis[4:]
            else:
                instruments.loc[i, 'Название станции (как в калькуляторе)'] = \
                    'не удалось сопоставить название'
                continue

            instruments.loc[i, 'Название станции (как в калькуляторе)'] = \
                calculator_departure_station

            # 2) rzd cost
            rzd_cost_report = await self._calculator_parser.get_rzd_cost_info(
                st1=calculator_departure_station,
                st2=calculator_arrival_station,
                fuel=calculator_fuel_name,
                weight=calculator_fuel_weight,
                capacity=66
            )
            rzd_cost = float(rzd_cost_report['sumtWithVat'])
            instruments.loc[i, 'РЖД стоимость'] = rzd_cost
            instruments.loc[i, 'РЖД стоимость + 10%'] = rzd_cost * 1.1

            # 3) total cost
            average_price = instruments.loc[i, 'Цена (за единицу измерения), руб - Средневзвешенная']
            if pd.notna(average_price):
                total_cost = average_price + rzd_cost * 1.1
                instruments.loc[i, 'Общая стоимость'] = total_cost

        # sort
        instruments.sort_values(
            by=['Общая стоимость',
                'РЖД стоимость + 10%',
                'Цена (за единицу измерения), руб - Средневзвешенная'],
            axis=0,
            ascending=[True, True, True],
            na_position='last',
            inplace=True
        )

        return instruments

    async def close(self):
        await self._calculator_parser.close()
        await self._trade_results_parser.close()
