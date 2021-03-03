from abc import abstractmethod
from email.message import EmailMessage
import mailbox
from typing import List, Optional, TypeVar, Union
from pydantic import PrivateAttr
from ..config import Path
from ..util import OpenClosable

T = TypeVar("T", bound="MailboxSender")


class MailboxSender(OpenClosable):  # ABC inherited from OpenClosable
    _mbox: Optional[mailbox.Mailbox] = PrivateAttr(None)

    @abstractmethod
    def _makebox(self) -> mailbox.Mailbox:
        ...

    def open(self) -> None:
        self._mbox = self._makebox()
        self._mbox.lock()

    def close(self) -> None:
        if self._mbox is None:
            raise ValueError("Mailbox is not open")
        self._mbox.unlock()
        self._mbox.close()
        self._mbox = None

    def send(self, msg: EmailMessage) -> None:
        with self:
            assert self._mbox is not None
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
