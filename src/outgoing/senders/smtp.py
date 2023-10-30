from __future__ import annotations
from email.message import EmailMessage
import logging
import smtplib
import sys
from typing import Optional
from pydantic import Field, PrivateAttr, ValidationInfo, field_validator
from ..config import NetrcConfig
from ..util import OpenClosable

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

STARTTLS = "starttls"

log = logging.getLogger(__name__)


class SMTPSender(NetrcConfig, OpenClosable):
    ssl: Literal[False, True, "starttls"] = False
    port: int = Field(0, ge=0, validate_default=True)
    _client: Optional[smtplib.SMTP] = PrivateAttr(None)

    @field_validator("port")
    @classmethod
    def _set_default_port(cls, v: int, info: ValidationInfo) -> int:
        if v == 0:
            ssl = info.data.get("ssl")
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
            log.debug(
                "Connecting to SMTP server at %s, port %d, using TLS",
                self.host,
                self.port,
            )
            self._client = smtplib.SMTP_SSL(self.host, self.port)
        else:
            log.debug("Connecting to SMTP server at %s, port %d", self.host, self.port)
            self._client = smtplib.SMTP(self.host, self.port)
        if self.ssl == STARTTLS:
            log.debug("Enabling STARTTLS")
            self._client.starttls()
        if self.username is not None:
            assert self.password is not None
            log.debug("Logging in as %r", self.username)
            self._client.login(self.username, self.password.get_secret_value())

    def close(self) -> None:
        if self._client is None:
            raise ValueError("SMTPSender is not open")
        log.debug("Closing connection to %s", self.host)
        self._client.quit()
        self._client = None

    def send(self, msg: EmailMessage) -> None:
        with self:
            assert self._client is not None
            log.info("Sending e-mail %r via SMTP", msg.get("Subject", "<NO SUBJECT>"))
            self._client.send_message(msg)
