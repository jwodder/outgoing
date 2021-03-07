from email.message import EmailMessage
from typing import Optional
from ..config import Path
from ..util import OpenClosable


class NullSender(OpenClosable):
    configpath: Optional[Path] = None

    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def send(self, msg: EmailMessage) -> None:
        ...
