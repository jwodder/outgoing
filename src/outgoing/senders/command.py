from email.message import EmailMessage
import logging
import subprocess
from pydantic import Field
from ..config import Path
from ..util import OpenClosable

log = logging.getLogger(__name__)


class CommandSender(OpenClosable):
    configpath: Path | None = None
    command: str | list[str] = Field(default_factory=lambda: ["sendmail", "-i", "-t"])

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        log.info(
            "Sending e-mail %r via command %r",
            msg.get("Subject", "<NO SUBJECT>"),
            self.command,
        )
        subprocess.run(
            self.command,
            shell=isinstance(self.command, str),
            input=bytes(msg),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
