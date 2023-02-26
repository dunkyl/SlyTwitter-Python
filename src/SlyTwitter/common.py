import re
from typing import ParamSpec, TypeVar, Any

RE_FILE_URL = re.compile(r'https?://[^\s]+\.(?P<extension>png|jpg|jpeg|gif|mp4|webp|webm)', re.IGNORECASE)

T_Params = ParamSpec('T_Params')
R = TypeVar('R')
S = TypeVar('S')
T = TypeVar('T')

class TwitterError(Exception):
    _obj: object

    def __init__(self, errorobj: Any) -> None:
        super().__init__()
        self._obj = errorobj