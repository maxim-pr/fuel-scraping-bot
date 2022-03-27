import pandas as pd

from scrapers.trade_results_scraper import TradeResultsScraper
from .utils import load_scraper_config


class DeliveryBasisReporter:
    """
    Provides report with fuel prices for given stations
    """

    def __init__(self, template_file_path: str, config_file_path: str):
        self._template_file_path = template_file_path
        config = load_scraper_config(config_file_path)
        self._trade_results_scraper = TradeResultsScraper(config)

    async def get_report(self) -> pd.DataFrame:
        instruments = await self._trade_results_scraper.get_all_instruments()
        report = pd.read_csv(self._template_file_path)
        report_dict = self._table_to_dict(report)

        for i in instruments.index:
            instrument_code = instruments.loc[i, 'Код Инструмента']
            if report_dict.get(instrument_code) is not None:
                ind, column = report_dict[instrument_code]
                average_price = instruments.loc[i, 'Цена (за единицу измерения), руб - Средневзвешенная']
                price_delta = instruments.loc[i, 'Изменение рыночной цены к цене предыдуего дня, руб']

                if pd.isna(average_price):
                    continue

                price_string = str(average_price)
                if pd.notna(price_delta):
                    price_string += f' ({price_delta})'
                report.loc[ind, column] = price_string

        return report

    @staticmethod
    def _table_to_dict(table: pd.DataFrame) -> dict[str, tuple[int, str]]:
        """
        :return: mapping of instrument codes to cell indices
        """

        table_dict = dict()
        for ind in table.index:
            for column in table.columns[3:]:
                instrument_code = table.loc[ind, column]
                if pd.notna(instrument_code):
                    table_dict[instrument_code] = (ind, column)
        return table_dict

    async def close(self):
        await self._trade_results_scraper.close()
