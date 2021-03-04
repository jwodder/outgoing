from email.message import EmailMessage
from mailbox import Maildir
from operator import itemgetter
from pathlib import Path
from typing import Optional
from email2dict import email2dict
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import MaildirSender


@pytest.mark.parametrize("folder", [None, "work"])
def test_maildir_construct(
    folder: Optional[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
            "folder": folder,
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MaildirSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
        "folder": folder,
    }
    assert sender._mbox is None


def test_maildir_send_no_folder_new_path(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    inbox = Maildir("inbox")
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])


def test_maildir_send_folder_new_path(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
            "folder": "work",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email1)
    inbox = Maildir("inbox")
    assert inbox.list_folders() == ["work"]
    work = inbox.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])


def test_maildir_send_no_folder_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = Maildir("inbox")
    inbox.add(test_email1)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 2
    msgs.sort(key=itemgetter("Subject"))
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert email2dict(test_email2) == email2dict(msgs[1])


def test_maildir_send_new_folder_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = Maildir("inbox")
    inbox.add(test_email1)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
            "folder": "work",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    assert inbox.list_folders() == ["work"]
    work = inbox.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email2) == email2dict(msgs[0])


def test_maildir_send_extant_folder_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = Maildir("inbox")
    inbox.add_folder("work").add(test_email1)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
            "folder": "work",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    assert inbox.list_folders() == ["work"]
    work = inbox.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 2
    msgs.sort(key=itemgetter("Subject"))
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert email2dict(test_email2) == email2dict(msgs[1])


def test_maildir_send_no_context(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    sender.send(test_email1)
    inbox = Maildir("inbox")
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])
