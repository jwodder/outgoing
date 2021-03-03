from email.message import EmailMessage
import subprocess
from typing import List, Optional, Union
from pydantic import Field
from ..config import Path
from ..util import OpenClosable


class CommandSender(OpenClosable):
    configpath: Optional[Path] = None
    command: Union[str, List[str]] = Field(
        default_factory=lambda: ["sendmail", "-i", "-t"]
    )

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        subprocess.run(
            self.command,
            shell=isinstance(self.command, str),
            input=bytes(msg),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
