from abc import ABC, abstractmethod
from email.message import EmailMessage
import mailbox
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, PrivateAttr
from ..config import Path

T = TypeVar("T", bound="MailboxSender")


class MailboxSender(BaseModel, ABC):
    _mbox: mailbox.Mailbox = PrivateAttr()

    def __init__(self, **data: Dict[str, Any]) -> None:
        super().__init__(**data)
        self._mbox = self._makebox()

    @abstractmethod
    def _makebox(self) -> mailbox.Mailbox:
        ...

    def __enter__(self: T) -> T:
        self._mbox.lock()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._mbox.close()

    def send(self, msg: EmailMessage) -> None:
        self._mbox.add(msg)


class MboxSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.mbox:
        return mailbox.mbox(self.path)


class MaildirSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path
    folder: Optional[str] = None

    def _makebox(self) -> mailbox.Maildir:
        box = mailbox.Maildir(self.path)
        if self.folder is not None:
            try:
                box = box.get_folder(self.folder)
            except mailbox.NoSuchMailboxError:
                box = box.add_folder(self.folder)
        return box


class MHSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path
    folder: Union[str, List[str], None] = None

    def _makebox(self) -> mailbox.MH:
        box = mailbox.MH(self.path)
        if self.folder is not None:
            folders: List[str]
            if isinstance(self.folder, str):
                folders = [self.folder]
            else:
                folders = self.folder
            for f in folders:
                try:
                    box = box.get_folder(f)
                except mailbox.NoSuchMailboxError:
                    box = box.add_folder(f)
        return box


class MMDFSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.MMDF:
        return mailbox.MMDF(self.path)


class BabylSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.Babyl:
        return mailbox.Babyl(self.path)
