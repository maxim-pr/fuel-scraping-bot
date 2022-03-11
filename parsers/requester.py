import asyncio
import logging
from time import monotonic

from aiohttp import ClientSession, ClientResponse


class Requester:
    """
    Wrapper around ClientSession to enable retries and logging
    """

    def __init__(
            self,
            session: ClientSession,
            init_timeout: float = 2,
            tries: int = 3
    ):
        if init_timeout <= 0:
            raise ValueError('init_timeout should be greater than 0')
        if tries < 1:
            raise ValueError('tries should be greater than 0')

        self._init_timeout = init_timeout
        self._tries = tries
        self._session = session
        self._logger = logging.getLogger(__name__)

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """
        Raises :class:`asyncio.TimeoutError`
        """

        timeout = self._init_timeout
        response = None

        for _ in range(self._tries):
            time_start = monotonic()
            try:
                response = await self._session.request(
                    method, url, timeout=timeout, **kwargs
                )
            except asyncio.TimeoutError:
                self._log_timeout(method, url, timeout)
            else:
                time_end = monotonic()
                self._log_response(response, time_end - time_start)
                if response.status < 500:
                    break
            finally:
                timeout *= 2

        if response:
            return response

        raise asyncio.TimeoutError()

    def _log_response(self, response: ClientResponse, time: float):
        log_message = f"{response.method} {response.url} " \
                      f"{response.status} {round(time * 1000, 3)}ms"
        if response.ok:
            self._logger.info(log_message)
        else:
            self._logger.error(log_message)

    def _log_timeout(self, method: str, url: str, timeout: float):
        self._logger.warning(f"{method.upper()} {url} {timeout}s timeout")
