from aiohttp import ClientSession
from bs4 import BeautifulSoup
from yarl import URL

from .errors import HtmlParsingError, ApiResponseError, InvalidStationError, \
    InvalidFuelError
from .requester import Requester
from .utils import to_multipart_form_data, ScraperConfig


class CalculatorScraper:
    def __init__(self, config: ScraperConfig):
        self._url = config.CALCULATOR_URL
        self._api_endpoint_url = config.API_ENDPOINT_URL
        self._session = ClientSession(raise_for_status=True)
        self._session.headers['Host'] = URL(self._url).host
        self._requester = Requester(self._session)
        self._sessid = None

    async def _init_request(self) -> str:
        """
        Initializes cookies and returns sessid (needed for further
        requests to API)

        Raises :class:`aiohttp.ClientResponseError`,
        :class:`asyncio.TimeoutError`, :class:`HtmlParsingError`
        """

        response = await self._requester.request(method='GET', url=self._url)
        response_html = await response.text()

        # retrieve sessid from response html page
        bs = BeautifulSoup(response_html, 'html.parser')
        sessid_tag = bs.find(id='sessid')
        if sessid_tag is None:
            raise HtmlParsingError('failed to retrieve sessid')

        sessid = sessid_tag.attrs['value']
        return sessid

    async def get_object_info(self, object_type: str,
                              object_name: str) -> dict[str, str]:
        """
        Returns info about the given object (either station or fuel) from API

        :param object_type: type of the object to get information about
        (should be either station or fuel)
        :param object_name: the name of the object
        :return: dictionary with information

        Raises ValueError, :class:`aiohttp.ClientResponseError`,
        :class:`asyncio.TimeoutError`, :class:`ApiResponseError`,
        :class:`InvalidStationError`, :class:`InvalidFuelError`
        """

        if object_type not in ('station', 'fuel'):
            raise ValueError(f'incorrect argument object_type: {object_type}. '
                             f'should be either station or fuel')

        # prepare sessid
        if self._sessid is None:
            self._sessid = await self._init_request()

        # set request data
        route = None
        if object_type == 'station':
            route = '/calculator/api/stations/filteredByNameOrCode/'
        elif object_type == "fuel":
            route = '/calculator/api/products/filteredByNameOrCode/'
        route += object_name

        form_data = to_multipart_form_data(
            {
                'action': 'getData',
                'sessid': self._sessid,
                'route': route,
                'limit': 1
            }
        )

        response = await self._requester.request(
            method='POST',
            url=self._api_endpoint_url,
            data=form_data
        )
        response_json = await response.json()

        if response_json.get('error'):
            raise ApiResponseError()

        if response_json['data'] is None:
            if object_type == 'station':
                raise InvalidStationError(object_name)
            elif object_type == 'fuel':
                raise InvalidFuelError(object_name)

        return response_json['data'][0]

    async def get_rzd_price_info(self, st1: str, st2: str,
                                 fuel: str, weight: int,
                                 capacity: int) -> dict[str, str]:
        """
        Retrieves rzd cost from API

        :param st1: departure station (e.g. Сургут)
        :param st2: arrival station (e.g. Комбинатская)
        :param fuel: name of the calculator fuel (e.g. ТОПЛИВО ДИЗЕЛЬНОЕ)
        :param weight: (e.g. 65)
        :param capacity: (e.g. 66)
        :return: information about RZD cost

        Raises :class:`aiohttp.ClientResponseError`,
        :class:`asyncio.TimeoutError`, :class:`ApiResponseError`
        """

        # prepare sessid
        if self._sessid is None:
            self._sessid = await self._init_request()

        # get stations' and fuel's codes
        st1_code = (await self.get_object_info(object_type='station',
                                               object_name=st1))['code']
        st2_code = (await self.get_object_info(object_type='station',
                                               object_name=st2))['code']
        fuel_code = (await self.get_object_info(object_type='fuel',
                                                object_name=fuel))['code']

        # set form data
        form_data = to_multipart_form_data(
            {
                'action': 'getCalculation',
                'sessid': self._sessid,
                'type': 43,  # тип вагона (43 - цистерны для нефтепродуктов)
                'st1': st1_code,  # код станции отправления
                'st2': st2_code,  # код станции назначения
                'kgr': fuel_code,  # код топлива
                'ves': weight,  # вес отправки на вагон
                'gp': capacity,  # грузоподьёмность
                'nv': 1,  # число вагонов
                'nvohr': 1,  # число охр. вагонов
                'nprov': 1,  # число проводников
                'osi': 4,  # число осей
                'sv': 2  # собственный вагон (1 - да, 2 - нет)
            }
        )

        # send request
        response = await self._requester.request(
            method='POST',
            url=self._api_endpoint_url,
            data=form_data
        )
        response_data = await response.json()

        if response_data.get('error'):
            raise ApiResponseError()
        if response_data['data'] is None:
            raise ApiResponseError('empty response data')

        return response_data['data']['total']

    async def close(self):
        await self._session.close()
