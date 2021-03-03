from email.message import EmailMessage
import smtplib
import sys
from typing import Any, Dict, Optional
from pydantic import PrivateAttr, validator
from ..config import NetrcConfig
from ..util import OpenClosable

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

STARTTLS = "starttls"


class SMTPSender(NetrcConfig, OpenClosable):
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

    def open(self) -> None:
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

    def close(self) -> None:
        if self._client is None:
            raise ValueError("SMTPSender is not open")
        self._client.quit()
        self._client = None

    def send(self, msg: EmailMessage) -> None:
        with self:
            assert self._client is not None
            self._client.send_message(msg)
