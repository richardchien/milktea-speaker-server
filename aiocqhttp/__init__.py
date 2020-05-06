import asyncio
import logging
import re
from typing import (Dict, Any, Optional, Callable, Union, List, Awaitable,
                    Coroutine)

try:
    import ujson as json
except ImportError:
    import json

from quart import Quart, abort, websocket

from .api_impl import AsyncApi, SyncApi, WebSocketReverseApi, ResultStore
from .bus import EventBus
from .exceptions import Error, TimingError
from .event import Event
from .message import Message, MessageSegment
from .utils import ensure_async

from . import exceptions
from .exceptions import *  # noqa: F401, F403

__all__ = [
    'CQHttp',
    'Event',
    'Message',
    'MessageSegment',
]
__all__ += exceptions.__all__

__pdoc__ = {}


def _deco_maker(type_: str) -> Callable:
    def deco_deco(self,
                  arg: Optional[Union[str, Callable]] = None,
                  *sub_event_names: str) -> Callable:
        def deco(func: Callable) -> Callable:
            if isinstance(arg, str):
                e = [type_ + '.' + e for e in [arg] + list(sub_event_names)]
                self.on(*e)(func)
            else:
                self.on(type_)(func)
            return func

        if isinstance(arg, Callable):
            return deco(arg)
        return deco

    return deco_deco


class CQHttp(AsyncApi):
    def __init__(self,
                 import_name: str = '',
                 *,
                 access_token: Optional[str] = None,
                 message_class: Optional[type] = Message,
                 server_app_kwargs: Optional[dict] = None,
                 **kwargs):
        self._wsr_api_clients = {}  # connected wsr api clients
        self._api = WebSocketReverseApi(self._wsr_api_clients, 60)
        self._sync_api = None

        self._access_token = access_token
        self._message_class = message_class
        self._bus = EventBus()
        self._loop = None

        self._server_app = Quart(import_name, **(server_app_kwargs or {}))
        self._server_app.before_serving(self._before_serving)
        self._server_app.add_websocket('/ws',
                                       strict_slashes=False,
                                       view_func=self._handle_wsr)

    async def _before_serving(self):
        self._loop = asyncio.get_running_loop()

    @property
    def asgi(self) -> Callable[[dict, Callable, Callable], Awaitable]:
        return self._server_app

    @property
    def server_app(self) -> Quart:
        return self._server_app

    @property
    def logger(self) -> logging.Logger:
        return self._server_app.logger

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._loop

    @property
    def api(self) -> AsyncApi:
        return self._api

    @property
    def sync(self) -> SyncApi:
        if not self._sync_api:
            if not self._loop:
                raise TimingError('attempt to access sync api '
                                  'before bot is running')
            self._sync_api = SyncApi(self._api, self._loop)
        return self._sync_api

    def run(self, host: str = None, port: int = None, *args, **kwargs) -> None:
        if 'use_reloader' not in kwargs:
            kwargs['use_reloader'] = False
        self._server_app.run(host=host, port=port, *args, **kwargs)

    def run_task(self,
                 host: str = None,
                 port: int = None,
                 *args,
                 **kwargs) -> Coroutine[None, None, None]:
        if 'use_reloader' not in kwargs:
            kwargs['use_reloader'] = False
        return self._server_app.run_task(host=host, port=port, *args, **kwargs)

    async def call_action(self, action: str, **params) -> Any:
        return await self._api.call_action(action=action, **params)

    async def send(self, event: Event, message: Union[str, Dict[str, Any],
                                                      List[Dict[str, Any]]],
                   **kwargs) -> Optional[Dict[str, Any]]:
        keys = {'type', 'detail_type', 'self_id'}
        params = {k: v for k, v in event.items() if k in keys}
        params['message'] = message
        params.update(kwargs)

        if 'detail_type' not in params:
            params['detail_type'] = 'private'

        return await self._api.call_action('send', **params)

    def subscribe(self, event_name: str, func: Callable) -> None:
        self._bus.subscribe(event_name, ensure_async(func))

    def unsubscribe(self, event_name: str, func: Callable) -> None:
        self._bus.unsubscribe(event_name, func)

    def on(self, *event_names: str) -> Callable:
        def deco(func: Callable) -> Callable:
            for name in event_names:
                self.subscribe(name, func)
            return func

        return deco

    on_message = _deco_maker('message')
    on_notice = _deco_maker('notice')
    on_request = _deco_maker('request')
    on_meta_event = _deco_maker('meta_event')

    async def _handle_wsr(self) -> None:
        if self._access_token:
            auth = websocket.headers.get('Authorization', '')
            m = re.fullmatch(r'(?:[Bb]earer) (?P<token>\S+)', auth)
            if not m:
                self.logger.warning('authorization header is missing')
                abort(401)

            token_given = m.group('token').strip()
            if token_given != self._access_token:
                self.logger.warning('authorization header is invalid')
                abort(403)

        self._add_wsr_api_client()
        try:
            while True:
                try:
                    payload = json.loads(await websocket.receive())
                except ValueError:
                    payload = None

                if not isinstance(payload, dict):
                    # ignore invalid payload
                    continue

                if 'type' in payload:
                    # is a event
                    asyncio.create_task(self._handle_event(payload))
                elif payload:
                    # is a api result
                    ResultStore.add(payload)
        finally:
            self._remove_wsr_api_client()

    def _add_wsr_api_client(self) -> None:
        ws = websocket._get_current_object()
        self_id = websocket.headers['X-Self-ID']
        self._wsr_api_clients[self_id] = ws

    def _remove_wsr_api_client(self) -> None:
        self_id = websocket.headers['X-Self-ID']
        if self_id in self._wsr_api_clients:
            # we must check the existence here,
            # because we allow wildcard ws connections,
            # that is, the self_id may be '*'
            del self._wsr_api_clients[self_id]

    async def _handle_event(self, payload: Dict[str, Any]) -> Any:
        ev = Event.from_payload(payload)
        if not ev:
            return

        event_name = ev.name
        self.logger.info(f'received event: {event_name}')

        if self._message_class and 'message' in ev:
            ev['message'] = self._message_class(ev['message'])
        results = list(
            filter(lambda r: r is not None, await
            self._bus.emit(event_name, ev)))
        # return the first non-none result
        return results[0] if results else None
