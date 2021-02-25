from email.message import EmailMessage
from types import TracebackType
from typing import Optional, Type
from pydantic import BaseModel
from ..config import Path


class NullSender(BaseModel):
    configpath: Optional[Path] = None

    def __enter__(self) -> "NullSender":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        pass
