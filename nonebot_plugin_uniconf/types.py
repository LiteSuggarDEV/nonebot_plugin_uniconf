from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypeVar

import watchfiles
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

CALLBACK_TYPE = Callable[[str, Path], Awaitable[Any]]
FILTER_TYPE = Callable[[watchfiles.main.FileChange], bool]
STRDICT = dict[str, Any]
BMODEL_T = TypeVar("BMODEL_T", STRDICT, list[str | STRDICT], str)

__all__ = [
    "BMODEL_T",
    "CALLBACK_TYPE",
    "FILTER_TYPE",
    "STRDICT",
    "T",
]
