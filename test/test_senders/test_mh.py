from __future__ import annotations
from email.message import EmailMessage
import logging
from mailbox import MH
from operator import itemgetter
from pathlib import Path
from mailbits import email2dict
import pytest
from outgoing import Sender, from_dict
from outgoing.senders.mailboxes import MHSender


@pytest.mark.parametrize("folder", [None, "work", ["important", "work"]])
def test_mh_construct(
    folder: str | list[str] | None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
            "folder": folder,
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, Sender)
    assert isinstance(sender, MHSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
        "folder": folder,
    }
    assert sender._mbox is None


def test_mh_send_no_folder_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    inbox = MH("inbox")
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening MH mailbox at {tmp_path / 'inbox'}, root folder",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to MH mailbox at"
            f" {tmp_path / 'inbox'}, root folder",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing MH mailbox at {tmp_path / 'inbox'}, root folder",
        ),
    ]


def test_mh_send_folder_str_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
            "folder": "work",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email1)
    inbox = MH("inbox")
    assert inbox.list_folders() == ["work"]
    work = inbox.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening MH mailbox at {tmp_path / 'inbox'}, folder 'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to MH mailbox at"
            f" {tmp_path / 'inbox'}, folder 'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing MH mailbox at {tmp_path / 'inbox'}, folder 'work'",
        ),
    ]


def test_mh_send_folder_list_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
            "folder": ["important", "work"],
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email1)
    inbox = MH("inbox")
    assert inbox.list_folders() == ["important"]
    important = inbox.get_folder("important")
    assert important.list_folders() == ["work"]
    work = important.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening MH mailbox at {tmp_path / 'inbox'}, folder 'important'/'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to MH mailbox at"
            f" {tmp_path / 'inbox'}, folder 'important'/'work'",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing MH mailbox at {tmp_path / 'inbox'}, folder 'important'/'work'",
        ),
    ]


def test_mh_send_no_folder_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MH("inbox")
    inbox.lock()
    inbox.add(test_email1)
    inbox.unlock()
    sender = from_dict(
        {
            "method": "mh",
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


def test_mh_send_folder_str_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MH("inbox")
    inbox.add(test_email1)
    sender = from_dict(
        {
            "method": "mh",
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


def test_mh_send_extant_folder_str_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MH("inbox")
    inbox.add_folder("work").add(test_email1)
    sender = from_dict(
        {
            "method": "mh",
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


def test_mh_send_folder_list_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MH("inbox")
    inbox.add(test_email1)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
            "folder": ["important", "work"],
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    assert inbox.list_folders() == ["important"]
    important = inbox.get_folder("important")
    assert important.list_folders() == ["work"]
    work = important.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email2) == email2dict(msgs[0])


def test_mh_send_partially_extant_folder_list(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MH("inbox")
    inbox.add_folder("important").add(test_email1)
    inbox.add_folder("work")
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
            "folder": ["important", "work"],
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    assert sorted(inbox.list_folders()) == ["important", "work"]
    assert list(inbox.get_folder("work")) == []
    important = inbox.get_folder("important")
    assert important.list_folders() == ["work"]
    work = important.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert email2dict(test_email2) == email2dict(msgs[0])


def test_mh_send_no_context(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    sender.send(test_email1)
    inbox = MH("inbox")
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])


def test_mh_close_unopened(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MHSender)
    with pytest.raises(ValueError) as excinfo:
        sender.close()
    assert str(excinfo.value) == "Mailbox is not open"
