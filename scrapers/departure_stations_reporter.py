import numpy as np
import pandas as pd

from .calculator_scraper import CalculatorScraper
from .trade_results_scraper import TradeResultsScraper
from .utils import load_scraper_config


class DepartureStationsReporter:
    """
    Provides report with list of stations sorted by fuel price + RZD price
    for provided fuel and arrival station
    """

    def __init__(self, config_file_path: str):
        self._config = load_scraper_config(config_file_path)
        self._trade_results_parser = TradeResultsScraper(self._config)
        self._calculator_scraper = CalculatorScraper(self._config)

    async def get_report(self, calculator_arrival_station: str,
                         fuel_name: str) -> pd.DataFrame:
        """

        :param calculator_arrival_station: name of arrival station
        AS IN CALCULATOR
        :param fuel_name:
        :return:
        """

        if fuel_name not in self._config.FUEL_NAME_TO_INSTRUMENT_CODES.keys():
            raise ValueError(
                f'fuel_name should be one of '
                f'{tuple(self._config.FUEL_NAME_TO_INSTRUMENT_CODES.keys())}'
            )

        # map fuel name to corresponding codes
        instrument_code_prefixes = self._config.FUEL_NAME_TO_INSTRUMENT_CODES[fuel_name]

        # map fuel name to calculator fuel name
        calculator_fuel_name = self._config.FUEL_NAME_TO_CALCULATOR_ITEM[fuel_name]
        calculator_fuel_weight = self._config.CALCULATOR_ITEM_WEIGHTS[calculator_fuel_name]

        all_instruments = await self._trade_results_parser.get_all_instruments()
        # filter all instruments by instrument code prefixes
        instruments = all_instruments.loc[
                            all_instruments['Код Инструмента'].str.startswith(
                                tuple(instrument_code_prefixes)
                            ), :
                        ]

        # add columns
        instruments.loc[:, 'Название станции (как в калькуляторе)'] = np.NaN
        instruments.loc[:, 'Название топлива (как в калькуляторе)'] = calculator_fuel_name
        instruments.loc[:, 'Вес топлива (проставляемый в калькуляторе)'] = calculator_fuel_weight
        instruments.loc[:, 'РЖД тариф'] = np.NaN
        instruments.loc[:, 'РЖД тариф + 10%'] = np.NaN
        instruments.loc[:, 'Итого'] = np.NaN

        # iterate through all the instruments
        for i in instruments.index:

            # 1) map delivery basis to calculator fuel name
            delivery_basis = instruments.loc[i, 'Базис поставки']
            if self._config.DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME.get(delivery_basis):
                calculator_departure_station = \
                    self._config.DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME[delivery_basis]
            elif delivery_basis.startswith('ст. '):
                calculator_departure_station = delivery_basis[4:]
            else:
                instruments.loc[i, 'Название станции (как в калькуляторе)'] = \
                    'не удалось сопоставить название'
                continue

            instruments.loc[i, 'Название станции (как в калькуляторе)'] = \
                calculator_departure_station

            # 2) rzd cost
            rzd_price_info = await self._calculator_scraper.get_rzd_price_info(
                st1=calculator_departure_station,
                st2=calculator_arrival_station,
                fuel=calculator_fuel_name,
                weight=calculator_fuel_weight,
                capacity=66
            )
            rzd_price = float(rzd_price_info['sumtWithVat'])
            instruments.loc[i, 'РЖД тариф'] = rzd_price
            instruments.loc[i, 'РЖД тариф + 10%'] = rzd_price * 1.1

            # 3) total cost
            fuel_price = instruments.loc[i, 'Цена (за единицу измерения), руб - Средневзвешенная']
            if pd.notna(fuel_price):
                total_cost = fuel_price + rzd_price * 1.1
                instruments.loc[i, 'Итого'] = total_cost

        # sort
        instruments.sort_values(
            by=['Итого',
                'РЖД тариф + 10%',
                'Цена (за единицу измерения), руб - Средневзвешенная'],
            axis=0,
            ascending=[True, True, True],
            na_position='last',
            inplace=True
        )

        return instruments

    async def close(self):
        await self._calculator_scraper.close()
        await self._trade_results_parser.close()
