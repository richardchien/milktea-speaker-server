import asyncio
import logging
from typing import Any, Optional, Callable, Awaitable

import aiocqhttp
from aiocqhttp import CQHttp

from .log import logger
from .sched import Scheduler

if Scheduler:
    scheduler = Scheduler()
else:
    scheduler = None


class NoneBot(CQHttp):
    def __init__(self, config_object: Optional[Any] = None):
        if config_object is None:
            from . import default_config as config_object

        config_dict = {
            k: v
            for k, v in config_object.__dict__.items()
            if k.isupper() and not k.startswith('_')
        }
        logger.debug(f'Loaded configurations: {config_dict}')
        super().__init__(message_class=aiocqhttp.message.Message,
                         **{k.lower(): v
                            for k, v in config_dict.items()})

        self.config = config_object
        self.asgi.debug = self.config.DEBUG

        from .message import handle_message

        @self.on_message
        async def _(event: aiocqhttp.Event):
            asyncio.create_task(handle_message(self, event))

    def run(self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            *args,
            **kwargs) -> None:
        host = host or self.config.HOST
        port = port or self.config.PORT
        if 'debug' not in kwargs:
            kwargs['debug'] = self.config.DEBUG

        logger.info(f'Running on {host}:{port}')
        super().run(host=host, port=port, *args, **kwargs)


_bot: Optional[NoneBot] = None


def init(config_object: Optional[Any] = None) -> None:
    """
    Initialize NoneBot instance.

    This function must be called at the very beginning of code,
    otherwise the get_bot() function will return None and nothing
    is gonna work properly.

    :param config_object: configuration object
    """
    global _bot
    _bot = NoneBot(config_object)

    if _bot.config.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    _bot.server_app.before_serving(_start_scheduler)


async def _start_scheduler():
    if scheduler and not scheduler.running:
        scheduler.configure(_bot.config.APSCHEDULER_CONFIG)
        scheduler.start()
        logger.info('Scheduler started')


def get_bot() -> NoneBot:
    """
    Get the NoneBot instance.

    The result is ensured to be not None, otherwise an exception will
    be raised.

    :raise ValueError: instance not initialized
    """
    if _bot is None:
        raise ValueError('NoneBot instance has not been initialized')
    return _bot


def run(host: Optional[str] = None,
        port: Optional[int] = None,
        *args,
        **kwargs) -> None:
    """Run the NoneBot instance."""
    get_bot().run(host=host, port=port, *args, **kwargs)


def on_startup(func: Callable[[], Awaitable[None]]) \
        -> Callable[[], Awaitable[None]]:
    """
    Decorator to register a function as startup callback.
    """
    return get_bot().server_app.before_serving(func)


from .exceptions import *
from .plugin import (load_plugin, load_plugins, load_builtin_plugins,
                     get_loaded_plugins)
from .message import message_preprocessor, Message, MessageSegment
from .command import on_command, CommandSession, CommandGroup
from .natural_language import (on_natural_language, NLPSession, NLPResult,
                               IntentCommand)
from .helpers import context_id

__all__ = [
    'NoneBot',
    'scheduler',
    'init',
    'get_bot',
    'run',
    'on_startup',
    'CQHttpError',
    'load_plugin',
    'load_plugins',
    'load_builtin_plugins',
    'get_loaded_plugins',
    'message_preprocessor',
    'Message',
    'MessageSegment',
    'on_command',
    'CommandSession',
    'CommandGroup',
    'on_natural_language',
    'NLPSession',
    'NLPResult',
    'IntentCommand',
    'context_id',
]
