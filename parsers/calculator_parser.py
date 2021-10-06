import json
import logging

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from .errors import HtmlParsingError, ApiError, InvalidStationError, InvalidFuelError
from .requester import Requester


class CalculatorParser:
    def __init__(self):
        self._CALCULATOR_URL = "https://spimex.com/markets/oil_products/rzd/"
        self._API_URL = "https://spimex.com/local/components/spimex/calculator.rzd/templates/.default/ajax.php"

        self._session = ClientSession(raise_for_status=True)
        self._session.headers["Host"] = "spimex.com"
        self._requester = Requester(self._session)
        self._sessid = None

        self._logger = logging.getLogger(__name__)

    async def _retrieve_sessid(self) -> str:
        """
        Initializes cookies and returns sessid

        Raises :class:`aiohttp.ClientError`, :class:`asyncio.TimeoutError`, :class:`HtmlParsingError`
        """

        response = await self._requester.request(method='GET', url=self._CALCULATOR_URL)
        response_text = await response.text()

        # retrieve sessid from response html page
        bs = BeautifulSoup(response_text, "html.parser")
        sessid_tag = bs.find(id="sessid")
        if sessid_tag is None:
            raise HtmlParsingError("failed to retrieve sessid")

        sessid = sessid_tag.attrs["value"]
        return sessid

    async def get_object_info(self, object_type: str, object_name: str) -> dict[str, str]:
        """
        Returns info about the given object (either station or fuel)

        Raises :class:`aiohttp.ClientError`, :class:`asyncio.TimeoutError`,
        :class:`ApiError`, :class:`InvalidStationError`, :class:`InvalidFuelError`

        :param object_type: type of the object to get information about (should be either station or fuel)
        :param object_name: the name of the object
        :return: dictionary with information
        """

        if object_type not in ("station", "fuel"):
            raise ValueError(f"incorrect argument object_type: {object_type}. should be either station or fuel")

        # prepare sessid
        if self._sessid is None:
            self._sessid = await self._retrieve_sessid()

        # set request data
        route = None
        if object_type == "station":
            route = "/calculator/api/stations/filteredByNameOrCode/"
        elif object_type == "fuel":
            route = "/calculator/api/products/filteredByNameOrCode/"
        route += object_name

        form_data = {
            "action": "getData",
            "sessid": self._sessid,
            "route": route,
            "limit": 1
        }

        self._logger.info(f"retrieving info about {object_type} {object_name}")
        response = await self._requester.request(
            method='POST',
            url=self._API_URL,
            data={
                "action": (None, form_data["action"]),
                "sessid": (None, form_data["sessid"]),
                "route": (None, form_data["route"]),
                "limit": (None, form_data["limit"])
            }
        )

        response_data = await response.json()
        self._logger.info(f"response json: {json.dumps(response_data, indent=2)}")

        if response_data.get("error"):
            raise ApiError()

        if response_data["data"] is None:
            if object_type == "station":
                raise InvalidStationError(object_name)
            elif object_type == "fuel":
                raise InvalidFuelError(object_name)

        return response_data["data"][0]

    async def get_rzd_cost_report(self, st1: str, st2: str, fuel: str, weight: int, capacity: int) -> dict[str, str]:
        """
        Retrieves rzd cost from API

        Raises :class:`aiohttp.ClientError`, :class:`asyncio.TimeoutError`, :class:`ApiError`

        :param st1: departure station (e.g. Сургут)
        :param st2: arrival station (e.g. Комбинатская)
        :param fuel: name of the calculator fuel (e.g. ТОПЛИВО ДИЗЕЛЬНОЕ)
        :param weight: (e.g. 65)
        :param capacity: (e.g. 66)
        :return: information about RZD cost
        """

        # prepare sessid
        if self._sessid is None:
            self._sessid = await self._retrieve_sessid()

        # get stations' and fuel's codes
        st1_code = (await self.get_object_info(object_type="station", object_name=st1))["code"]
        st2_code = (await self.get_object_info(object_type="station", object_name=st2))["code"]
        fuel_code = (await self.get_object_info(object_type="fuel", object_name=fuel))["code"]

        # set form data
        form_data = {
            "action": "getCalculation",
            "sessid": self._sessid,
            "type": 43,  # тип вагона (43 - цистерны для нефтепродуктов)
            "st1": st1_code,  # код станции отправления
            "st2": st2_code,  # код станции назначения
            "kgr": fuel_code,  # код топлива
            "ves": weight,  # вес отправки на вагон
            "gp": capacity,  # грузоподьёмность
            "nv": 1,  # число вагонов
            "nvohr": 1,  # число охр. вагонов
            "nprov": 1,  # число проводников
            "osi": 4,  # число осей
            "sv": 2  # собственный вагон (1 - да, 2 - нет)
        }

        # send request
        self._logger.info(f'{st1} -> {st2}; fuel: {fuel}; weight: {weight}; capacity: {capacity}')
        response = await self._requester.request(
            method='POST',
            url=self._API_URL,
            data={
                "action": (None, form_data["action"]),
                "sessid": (None, form_data["sessid"]),
                "type": (None, form_data["type"]),
                "st1": (None, form_data["st1"]),
                "st2": (None, form_data["st2"]),
                "kgr": (None, form_data["kgr"]),
                "ves": (None, form_data["ves"]),
                "gp": (None, form_data["gp"]),
                "nv": (None, form_data["nv"]),
                "nvohr": (None, form_data["nvohr"]),
                "nprov": (None, form_data["nprov"]),
                "osi": (None, form_data["osi"]),
                "sv": (None, form_data["sv"])
            }
        )

        response_data = await response.json()
        self._logger.info(f"response JSON: {json.dumps(response_data, indent=2)}")

        if response_data.get("error"):
            raise ApiError()

        if response_data["data"] is None:
            raise ApiError("empty response data")

        return response_data["data"]["total"]

    async def close(self):
        await self._session.close()
