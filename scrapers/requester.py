import asyncio
import logging
from time import monotonic

from aiohttp import ClientSession, ClientResponse

logger = logging.getLogger(__name__)


class Requester:
    """
    Wrapper around ClientSession to enable retries and log requests
    """

    def __init__(self, session: ClientSession,
                 init_timeout: float = 2, num_tries: int = 3):
        if init_timeout <= 0:
            raise ValueError('init_timeout should be greater than 0')
        if num_tries < 1:
            raise ValueError('num_tries should be greater than 0')

        self._init_timeout = init_timeout
        self._num_tries = num_tries
        self._session = session

    async def request(self, method: str, url: str, **kwargs) -> ClientResponse:
        """
        Raises :class:`asyncio.TimeoutError`
        """

        timeout = self._init_timeout
        response = None

        for _ in range(self._num_tries):
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

        if response is None:
            raise asyncio.TimeoutError()

        return response

    @staticmethod
    def _log_response(response: ClientResponse, time: float):
        log_message = ' '.join(
            (
                'request',
                f'method={response.method}',
                f'url={response.url}',
                f'status={response.status}',
                f'time={round(time * 1000, 3)}ms'
            )
        )
        if response.ok:
            logger.info(log_message)
        else:
            logger.error(log_message)

    @staticmethod
    def _log_timeout(method: str, url: str, timeout: float):
        log_message = ' '.join(
            (
                'request',
                f'method={method.upper()}',
                f'url={url}',
                f'timeout={timeout}s'
            )
        )
        logger.warning(log_message)
