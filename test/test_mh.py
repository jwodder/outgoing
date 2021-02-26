from email.message import EmailMessage
from mailbox import MH
from pathlib import Path
from typing import List, Union, cast
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import MHSender
from testing_lib import assert_emails_eq, msg_factory, test_email1


@pytest.mark.parametrize("folder", [None, "work", ["important", "work"]])
def test_mh_construct(
    folder: Union[str, List[str], None], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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
    assert isinstance(sender, MHSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
        "folder": folder,
    }
    assert sender._mbox is None


def test_mh_send_no_folder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mh",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email1)
    inbox = MH("inbox", factory=msg_factory)  # type: ignore[arg-type]
    assert inbox.list_folders() == []
    msgs = list(inbox)
    assert len(msgs) == 1
    assert_emails_eq(test_email1, cast(EmailMessage, msgs[0]))


def test_mh_send_folder_str(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
    inbox = MH("inbox", factory=msg_factory)  # type: ignore[arg-type]
    assert inbox.list_folders() == ["work"]
    work = inbox.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert_emails_eq(test_email1, cast(EmailMessage, msgs[0]))


def test_mh_send_folder_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
    inbox = MH("inbox", factory=msg_factory)  # type: ignore[arg-type]
    assert inbox.list_folders() == ["important"]
    important = inbox.get_folder("important")
    assert important.list_folders() == ["work"]
    work = important.get_folder("work")
    msgs = list(work)
    assert len(msgs) == 1
    assert_emails_eq(test_email1, cast(EmailMessage, msgs[0]))
