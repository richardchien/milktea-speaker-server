from anybot import Event

from . import NoneBot
from .helpers import send
from .typing import Message_T


class BaseSession:
    __slots__ = ('bot', 'event')

    def __init__(self, bot: NoneBot, event: Event):
        self.bot = bot
        self.event = event

    @property
    def ctx(self) -> Event:
        return self.event

    @ctx.setter
    def ctx(self, val: Event) -> None:
        self.event = val

    async def send(self,
                   message: Message_T,
                   *,
                   ignore_failure: bool = True,
                   **kwargs) -> None:
        """
        Send a message ignoring failure by default.

        :param message: message to send
        :param ignore_failure: if any Error raised, ignore it
        :return: the result returned by client
        """
        return await send(self.bot,
                          self.event,
                          message,
                          ignore_failure=ignore_failure,
                          **kwargs)
