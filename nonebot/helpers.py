import hashlib
import random
from typing import Sequence, Callable, Any

from anybot import Event

from . import NoneBot
from .exceptions import Error
from .message import escape
from .typing import Message_T, Expression_T


def context_id(event: Event, *, use_hash: bool = False) -> str:
    """
    Calculate a unique id representing the context of the given event.

    :param event: the event object
    :param use_hash: use md5 to hash the id or not
    """
    ctx_id = f'/self/{event.self_id}'
    if ctx_id and use_hash:
        ctx_id = hashlib.md5(ctx_id.encode('ascii')).hexdigest()
    return ctx_id


async def send(bot: NoneBot,
               event: Event,
               message: Message_T,
               *,
               ignore_failure: bool = True,
               **kwargs) -> Any:
    """Send a message ignoring failure by default."""
    try:
        return await bot.send(event, message, **kwargs)
    except Error:
        if not ignore_failure:
            raise
        return None


def render_expression(expr: Expression_T,
                      *args,
                      escape_args: bool = True,
                      **kwargs) -> str:
    """
    Render an expression to message string.

    :param expr: expression to render
    :param escape_args: should escape arguments or not
    :param args: positional arguments used in str.format()
    :param kwargs: keyword arguments used in str.format()
    :return: the rendered message
    """
    if isinstance(expr, Callable):
        expr = expr(*args, **kwargs)
    elif isinstance(expr, Sequence) and not isinstance(expr, str):
        expr = random.choice(expr)
    if escape_args:
        return expr.format(
            *[escape(s) if isinstance(s, str) else s for s in args], **{
                k: escape(v) if isinstance(v, str) else v
                for k, v in kwargs.items()
            })
    return expr.format(*args, **kwargs)
