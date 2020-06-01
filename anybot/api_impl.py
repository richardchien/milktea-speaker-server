import abc
import asyncio
import sys
from typing import Dict, Any

try:
    import ujson as json
except ImportError:
    import json

from quart import websocket as event_ws
from quart.wrappers.request import Websocket

from .api import Api
from .exceptions import ActionFailed, ApiNotAvailable, NetworkError
from .utils import sync_wait


class AsyncApi(Api):
    @abc.abstractmethod
    async def call_action(self, action: str, **params) -> Any:
        pass


class _SequenceGenerator:
    _seq = 1

    @classmethod
    def next(cls) -> int:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return s


class ResultStore:
    _futures: Dict[int, asyncio.Future] = {}

    @classmethod
    def add(cls, result: Dict[str, Any]):
        if isinstance(result.get('echo'), dict) and \
                isinstance(result['echo'].get('seq'), int):
            future = cls._futures.get(result['echo']['seq'])
            if future:
                future.set_result(result)

    @classmethod
    async def fetch(cls, seq: int, timeout_sec: float) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[seq] = future
        try:
            return await asyncio.wait_for(future, timeout_sec)
        except asyncio.TimeoutError:
            # haven't received any result until timeout,
            # we consider this API call failed with a network error.
            raise NetworkError('WebSocket API call timeout')
        finally:
            # don't forget to remove the future object
            del cls._futures[seq]


class WebSocketReverseApi(AsyncApi):
    def __init__(self, connected_clients: Dict[str, Websocket],
                 timeout_sec: float):
        super().__init__()
        self._clients = connected_clients
        self._timeout_sec = timeout_sec

    async def call_action(self, action: str, **params) -> Any:
        api_ws = None
        if params.get('self_id'):
            # 明确指定
            api_ws = self._clients.get(str(params['self_id']))
        elif event_ws and event_ws.headers['X-Self-ID'] in self._clients:
            # 没有指定，但在事件处理函数中
            api_ws = self._clients.get(event_ws.headers['X-Self-ID'])
        elif len(self._clients) == 1:
            # 没有指定，不在事件处理函数中，但只有一个连接
            api_ws = tuple(self._clients.values())[0]

        if not api_ws:
            raise ApiNotAvailable

        seq = _SequenceGenerator.next()
        await api_ws.send(
            json.dumps({
                'action': action,
                'params': params,
                'echo': {
                    'seq': seq
                }
            }, ensure_ascii=False))

        result = await ResultStore.fetch(seq, self._timeout_sec)
        if isinstance(result, dict):
            if result.get('status') == 'failed':
                raise ActionFailed(retcode=result.get('retcode'))
        return result.get('data')


class SyncApi(Api):
    def __init__(self, async_api: AsyncApi, loop: asyncio.AbstractEventLoop):
        self._async_api = async_api
        self._loop = loop

    def call_action(self, action: str, **params) -> Any:
        return sync_wait(coro=self._async_api.call_action(action, **params),
                         loop=self._loop)
