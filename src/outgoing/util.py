from abc import ABC, abstractmethod
import os
from pathlib import Path
from types import TracebackType
from typing import Optional, Type, TypeVar, Union
from pydantic import BaseModel, PrivateAttr

AnyPath = Union[str, bytes, "os.PathLike[str]", "os.PathLike[bytes]"]

OC = TypeVar("OC", bound="OpenClosable")


class OpenClosable(ABC, BaseModel):
    _context_depth: int = PrivateAttr(0)

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def __enter__(self: OC) -> OC:
        if self._context_depth == 0:
            self.open()
        self._context_depth += 1
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._context_depth -= 1
        if self._context_depth == 0:
            self.close()


def resolve_path(path: AnyPath, basepath: Optional[AnyPath] = None) -> Path:
    p = Path(os.fsdecode(path)).expanduser()
    if basepath is not None:
        p = Path(os.fsdecode(basepath)).parent / p
    return p.resolve()
