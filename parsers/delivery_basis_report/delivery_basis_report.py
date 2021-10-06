import pandas as pd

from ..trade_results_parser import TradeResultsParser


class DeliveryBasisReporter:
    def __init__(self, template_file_path: str):
        self._template_file_path = template_file_path
        self._trade_results_parser = TradeResultsParser()

    async def get_report(self):
        instruments = await self._trade_results_parser.retrieve_all_instruments()
        template = self._load_template()
        template_dict = self._template_to_dict(template)

        for i in instruments.index:
            instrument_code = instruments.loc[i, 'Код Инструмента']
            if instrument_code in template_dict:
                index_position, column_name = template_dict[instrument_code]
                average_price = instruments.loc[i, 'Цена (за единицу измерения), руб - Средневзвешенная']
                price_delta = instruments.loc[i, 'Изменение рыночной цены к цене предыдуего дня, руб']

                if pd.isna(average_price):
                    continue

                price_string = str(average_price)
                if pd.notna(price_delta):
                    price_string += f"({price_delta})"
                template.loc[index_position, column_name] = price_string

        return template

    def _load_template(self) -> pd.DataFrame:
        template = pd.read_csv(self._template_file_path)
        return template

    def _template_to_dict(self, template: pd.DataFrame) -> dict[str, tuple[int, int]]:
        fuel_columns = template.columns[3:]
        fuels: pd.DataFrame = template.loc[:, fuel_columns]
        template_dict = dict()

        for i in fuels.index:
            for j in fuels.columns:
                if pd.notna(fuels.loc[i, j]):
                    template_dict[fuels.loc[i, j]] = (i, j)

        return template_dict

    async def close(self):
        await self._trade_results_parser.close()
