from email.message import EmailMessage
import subprocess
from types import TracebackType
from typing import Optional, Type
from pydantic import BaseModel
from ..config import Path


class CommandSender(BaseModel):
    configpath: Optional[Path] = None
    command: str = "sendmail -i -t"

    def __enter__(self) -> "CommandSender":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        subprocess.run(
            self.command,
            shell=True,
            input=bytes(msg),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
