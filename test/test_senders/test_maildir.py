from email.message import EmailMessage
import logging
from mailbox import Maildir
from operator import itemgetter
from pathlib import Path
from mailbits import email2dict
import pytest
from outgoing import Sender, from_dict
from outgoing.senders.mailboxes import MaildirSender


@pytest.mark.parametrize("folder", [None, "work"])
def test_maildir_construct(
    folder: str | None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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
    assert isinstance(sender, Sender)
    assert isinstance(sender, MaildirSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
        "folder": folder,
    }
    assert sender._mbox is None


def test_maildir_send_no_folder_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
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
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening Maildir at {tmp_path / 'inbox'}, root folder",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to Maildir at"
            f" {tmp_path / 'inbox'}, root folder",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing Maildir at {tmp_path / 'inbox'}, root folder",
        ),
    ]


def test_maildir_send_folder_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
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
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening Maildir at {tmp_path / 'inbox'}, folder 'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to Maildir at"
            f" {tmp_path / 'inbox'}, folder 'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing Maildir at {tmp_path / 'inbox'}, folder 'work'",
        ),
    ]


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


def test_maildir_close_unopened(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "maildir",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MaildirSender)
    with pytest.raises(ValueError) as excinfo:
        sender.close()
    assert str(excinfo.value) == "Mailbox is not open"
