from email.message import EmailMessage
import logging
from ..config import Path
from ..util import OpenClosable

log = logging.getLogger(__name__)


class NullSender(OpenClosable):
    configpath: Path | None = None

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, msg: EmailMessage) -> None:
        log.info("Discarding e-mail %r", msg.get("Subject", "<NO SUBJECT>"))
