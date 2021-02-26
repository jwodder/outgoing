from email.message import EmailMessage
from mailbox import mbox
from pathlib import Path
from typing import cast
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import MboxSender
from testing_lib import assert_emails_eq, msg_factory, test_email1


def test_mbox_construct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MboxSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
    }
    assert sender._mbox is None


def test_mbox_send(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email1)
    inbox = mbox("inbox", factory=msg_factory)  # type: ignore[arg-type]
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    assert_emails_eq(test_email1, cast(EmailMessage, msgs[0]))
