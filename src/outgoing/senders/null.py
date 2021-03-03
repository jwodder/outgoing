from email.message import EmailMessage
from typing import Optional
from ..config import Path
from ..util import OpenClosable


class NullSender(OpenClosable):
    configpath: Optional[Path] = None

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        pass
