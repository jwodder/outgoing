from email.message import EmailMessage
import smtplib
import sys
from types import TracebackType
from typing import Any, Dict, Optional, Type
from pydantic import PrivateAttr
from ..config import NetrcConfig

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

STARTTLS = "starttls"


class SMTPSender(NetrcConfig):
    port: int = 0
    ssl: Literal[False, True, "starttls"] = False
    _client: smtplib.SMTP = PrivateAttr()

    def __init__(self, **data: Dict[str, Any]) -> None:
        super().__init__(**data)
        if self.ssl and self.ssl != STARTTLS:
            if self.port == 0:
                self.port = 465
            self._client = smtplib.SMTP_SSL()
        else:
            if self.port == 0:
                self.port = 587 if self.ssl == STARTTLS else 25
            self._client = smtplib.SMTP()

    def __enter__(self) -> "SMTPSender":
        self._client.connect(self.host, self.port)
        if self.ssl == STARTTLS:
            self._client.starttls()
        auth = self.get_username_password()
        if auth is not None:
            self._client.login(auth[0], auth[1])
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._client.quit()

    def send(self, msg: EmailMessage) -> None:
        self._client.send_message(msg)
