from   email.message import EmailMessage
import mailbox
from   types         import TracebackType
from   typing        import Any, Dict, Optional, Type
from   pydantic      import BaseModel, PrivateAttr
from   ..config      import Path

class MboxSender(BaseModel):
    configpath: Optional[Path] = None
    path: Path
    _mbox: mailbox.mbox = PrivateAttr()

    def __init__(self, **data: Dict[str, Any]) -> None:
        super().__init__(**data)
        self._mbox = mailbox.mbox(self.path)

    def __enter__(self) -> "MboxSender":
        self._mbox.lock()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._mbox.close()
        pass

    def send(self, msg: EmailMessage) -> None:
        self._mbox.add(msg)
