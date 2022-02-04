import logging

import numpy as np
import pandas as pd
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from .errors import HtmlParsingError
from parsers.requester import Requester


class TradeResultsScraper:
    def __init__(self):
        self._URL = "https://spimex.com/markets/oil_products/trades/results/"

        self._session = ClientSession(raise_for_status=True)
        self._session.headers["Host"] = "spimex.com"
        self._requester = Requester(self._session)

        self._logger = logging.getLogger(__name__)

    async def _retrieve_trade_results(self) -> pd.DataFrame:
        """
        Downloads the latest trade results from the website

        Raises :class:`aiohttp.ClientError`, :class:`asyncio.TimeoutError`, :class:`HtmlParsingError`
        """

        self._logger.info('retrieving link to trade results xl file')
        response = await self._requester.request(method='GET', url=self._URL)
        response_html = await response.text()

        # get url from html page
        bs = BeautifulSoup(response_html, 'html.parser')
        uri = bs.find('a', class_="accordeon-inner__item-title link xls").attrs['href']
        if uri is None:
            raise HtmlParsingError("failed to retrieve url to the trade results file")
        trade_results_file_url = "https://spimex.com/" + uri

        # download the xl file and compose DataFrame out of it
        self._logger.info('retrieving trade results xl file')
        response = await self._requester.request(method='GET', url=trade_results_file_url)
        response_content = await response.content.read()
        trade_results = pd.read_excel(response_content, sheet_name='TRADE_SUMMARY')
        return trade_results

    def _preprocess_trade_results(self, trade_results: pd.DataFrame):
        # delete 0th column
        trade_results.drop(columns=[trade_results.columns[0]], inplace=True)

        # drop unnecessary rows in the beginning
        trade_results.drop(index=trade_results.index[:7], inplace=True)

        # drop last 2 rows in the end
        trade_results.drop(index=trade_results.index[-2:], inplace=True)

        # assign column names
        trade_results.columns = ['Код Инструмента',
                                 'Наименование Инструмента',
                                 'Базис поставки',
                                 'Объем Договоров в единицах измерения',
                                 'Обьем Договоров, руб',
                                 'Изменение рыночной цены к цене предыдуего дня, руб',
                                 'Изменение рыночной цены к цене предыдуего дня, %',
                                 'Цена (за единицу измерения), руб - Минимальная',
                                 'Цена (за единицу измерения), руб - Средневзвешенная',
                                 'Цена (за единицу измерения), руб - Максимальная',
                                 'Цена (за единицу измерения), руб - Рыночная',
                                 'Цена в Заявках (за единицу измерения) - Лучшее предложение',
                                 'Цена в Заявках (за единицу измерения) - Лучший спрос',
                                 'Количество Договоров, шт']

        # assign index
        trade_results.index = range(trade_results.shape[0])

        # replace - with NaN values
        trade_results.replace('-', np.NaN, inplace=True)

        # convert column to float type
        trade_results['Цена (за единицу измерения), руб - Средневзвешенная'] = \
            pd.to_numeric(trade_results['Цена (за единицу измерения), руб - Средневзвешенная'])
        trade_results['Изменение рыночной цены к цене предыдуего дня, руб'] = \
            pd.to_numeric(trade_results['Изменение рыночной цены к цене предыдуего дня, руб'])

    async def retrieve_all_instruments(self) -> pd.DataFrame:
        """
        Raises :class:`aiohttp.ClientError`, :class:`asyncio.TimeoutError`, :class:`HtmlParsingError`

        :return: DataFrame of all instruments
        """
        trade_results = await self._retrieve_trade_results()
        self._preprocess_trade_results(trade_results)

        return trade_results.loc[
               :,
               [
                   'Код Инструмента',
                   'Наименование Инструмента',
                   'Базис поставки',
                   'Цена (за единицу измерения), руб - Средневзвешенная',
                   'Изменение рыночной цены к цене предыдуего дня, руб'
               ]]

    async def close(self):
        await self._session.close()
