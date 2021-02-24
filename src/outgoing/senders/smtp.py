from   email.message import EmailMessage
import smtplib
import sys
from   types         import TracebackType
from   typing        import Any, Dict, Optional, Type
from   pydantic      import BaseModel, PrivateAttr, root_validator
from   ..config      import Password, Path

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

STARTTLS = "starttls"

class SMTPPassword(Password):
    host_field = "host"
    username_field = "username"


class SMTPSender(BaseModel):
    configpath: Optional[Path] = None
    host: str
    username: Optional[str] = None
    password: Optional[SMTPPassword] = None
    port: int = 0
    ssl: Literal[False, True, "starttls"] = False
    _client: smtplib.SMTP = PrivateAttr()

    @root_validator
    def _require_username_iff_password(
        cls,  # noqa: B902
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        if (values.get("username") is None) != (values.get("password") is None):
            raise ValueError(
                "Username cannot be given without password and vice versa"
            )
        return values

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
        username = self.username
        password = self.password
        if username is not None:
            assert password is not None
            self._client.login(username, password.get_secret_value())
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
