from __future__ import annotations
from abc import abstractmethod
from email.message import EmailMessage
import logging
import mailbox
from typing import List, Optional, Union
from pydantic import PrivateAttr
from ..config import Path
from ..util import OpenClosable

log = logging.getLogger(__name__)


class MailboxSender(OpenClosable):  # ABC inherited from OpenClosable
    _mbox: Optional[mailbox.Mailbox] = PrivateAttr(None)

    @abstractmethod
    def _makebox(self) -> mailbox.Mailbox: ...

    @abstractmethod
    def _describe(self) -> str: ...

    def open(self) -> None:
        log.debug("Opening %s", self._describe())
        self._mbox = self._makebox()
        self._mbox.lock()

    def close(self) -> None:
        if self._mbox is None:
            raise ValueError("Mailbox is not open")
        log.debug("Closing %s", self._describe())
        self._mbox.unlock()
        self._mbox.close()
        self._mbox = None

    def send(self, msg: EmailMessage) -> None:
        with self:
            assert self._mbox is not None
            log.info(
                "Adding e-mail %r to %s",
                msg.get("Subject", "<NO SUBJECT>"),
                self._describe(),
            )
            self._mbox.add(msg)


class MboxSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.mbox:
        return mailbox.mbox(self.path)

    def _describe(self) -> str:
        return f"mbox at {self.path}"


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

    def _describe(self) -> str:
        if self.folder is None:
            folder = "root folder"
        else:
            folder = f"folder {self.folder!r}"
        return f"Maildir at {self.path}, {folder}"


class MHSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path
    folder: Union[str, List[str], None] = None

    def _makebox(self) -> mailbox.MH:
        box = mailbox.MH(self.path)
        if self.folder is not None:
            folders: list[str]
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

    def _describe(self) -> str:
        if self.folder is None:
            folder = "root folder"
        elif isinstance(self.folder, str):
            folder = f"folder {self.folder!r}"
        else:
            folder = "folder " + "/".join(map(repr, self.folder))
        return f"MH mailbox at {self.path}, {folder}"


class MMDFSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.MMDF:
        return mailbox.MMDF(self.path)

    def _describe(self) -> str:
        return f"MMDF mailbox at {self.path}"


class BabylSender(MailboxSender):
    configpath: Optional[Path] = None
    path: Path

    def _makebox(self) -> mailbox.Babyl:
        return mailbox.Babyl(self.path)

    def _describe(self) -> str:
        return f"Babyl mailbox at {self.path}"
