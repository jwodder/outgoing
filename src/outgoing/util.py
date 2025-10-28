from __future__ import annotations
from abc import ABC, abstractmethod
import os
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, TypeAlias
from pydantic import BaseModel, PrivateAttr

if TYPE_CHECKING:
    from typing_extensions import Self

AnyPath: TypeAlias = str | bytes | os.PathLike[str] | os.PathLike[bytes]


class OpenClosable(ABC, BaseModel):
    """
    An abstract base class for creating reentrant_ context managers.  A
    concrete subclass must define ``open()`` and ``close()`` methods;
    `OpenClosable` will then define ``__enter__`` and ``__exit__`` methods that
    keep track of the depth of nested ``with`` statements, calling ``open()``
    and ``close()`` only when entering & exiting the outermost ``with``.

    .. _reentrant: https://docs.python.org/3/library/contextlib.html
                   #reentrant-cms
    """

    _context_depth: int = PrivateAttr(0)

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> Self:
        if self._context_depth == 0:
            self.open()
        self._context_depth += 1
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        self._context_depth -= 1
        if self._context_depth == 0:
            self.close()


def resolve_path(path: AnyPath, basepath: AnyPath | None = None) -> Path:
    """
    Convert a path to a `pathlib.Path` instance and resolve it using the same
    rules for as paths in ``outgoing`` configuration files: expand tildes by
    calling `Path.expanduser()`, prepend the parent directory of ``basepath``
    (usually the value of ``configpath``) to the path if given, and then
    resolve the resulting path to make it absolute.

    :param path path: the path to resolve
    :param path basepath: an optional path to resolve ``path`` relative to
    :rtype: pathlib.Path
    """
    p = Path(os.fsdecode(path)).expanduser()
    if basepath is not None:
        p = Path(os.fsdecode(basepath)).parent / p
    return p.resolve()
