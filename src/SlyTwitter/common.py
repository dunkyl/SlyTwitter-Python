import re
from typing import ParamSpec, TypeVar, Callable, Concatenate, Awaitable

RE_FILE_URL = re.compile(r'https?://[^\s]+\.(?P<extension>png|jpg|jpeg|gif|mp4)', re.IGNORECASE)

T_Params = ParamSpec('T_Params')
R = TypeVar('R')
S = TypeVar('S')
T = TypeVar('T')

def make_with_self(constructor: Callable[[T, S], R]) -> Callable[
        [Callable[Concatenate[S, T_Params], Awaitable[T]]]
        , Callable[Concatenate[S, T_Params], Awaitable[R]]]:
    def decorator(func: Callable[Concatenate[S, T_Params], Awaitable[T]]) -> Callable[Concatenate[S, T_Params], Awaitable[R]]:
        async def wrapper(self: S, *args: T_Params.args, **kwargs: T_Params.kwargs) -> R:
            result = await func(self, *args, **kwargs)
            return constructor(result, self)
        return wrapper
    return decorator

class TwitterError(Exception):
    _obj: object

    def __init__(self, errorobj) -> None:
        super().__init__()
        self._obj = errorobj