from typing import Union, List, Dict, Any, Sequence, Callable, Tuple, Awaitable

from anybot.typing import Message_T

Context_T = Dict[str, Any]
Expression_T = Union[str, Sequence[str], Callable]
CommandName_T = Tuple[str, ...]
CommandArgs_T = Dict[str, Any]
State_T = Dict[str, Any]
Filter_T = Callable[[Any], Union[Any, Awaitable[Any]]]
