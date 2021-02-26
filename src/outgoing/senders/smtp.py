from email.message import EmailMessage
import smtplib
import sys
from types import TracebackType
from typing import Any, Dict, Optional, Type
from pydantic import PrivateAttr, validator
from ..config import NetrcConfig

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

STARTTLS = "starttls"


class SMTPSender(NetrcConfig):
    ssl: Literal[False, True, "starttls"] = False
    port: int = 0
    _client: Optional[smtplib.SMTP] = PrivateAttr(None)

    @validator("port", always=True)
    def _set_default_port(cls, v: Any, values: Dict[str, Any]) -> Any:  # noqa: B902
        if v == 0:
            ssl = values.get("ssl")
            if ssl is True:
                return 465
            elif ssl == STARTTLS:
                return 587
            else:
                return 25
        else:
            return v

    def __enter__(self) -> "SMTPSender":
        # We need to pass the host & port to the constructor instead of calling
        # connect() later due to <https://bugs.python.org/issue36094>.
        if self.ssl is True:
            self._client = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self._client = smtplib.SMTP(self.host, self.port)
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
        assert self._client is not None
        self._client.quit()

    def send(self, msg: EmailMessage) -> None:
        assert self._client is not None, "Not inside a context"
        self._client.send_message(msg)
