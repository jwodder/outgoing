from email.message import EmailMessage
from mailbox import Babyl
from pathlib import Path
from email2dict import email2dict
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import BabylSender


def test_babyl_construct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "babyl",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, BabylSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
    }
    assert sender._mbox is None


def test_babyl_send_new_path(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "babyl",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    inbox = Babyl("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])


def test_babyl_send_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = Babyl("inbox")
    inbox.lock()
    inbox.add(test_email1)
    inbox.close()
    sender = from_dict(
        {
            "method": "babyl",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    inbox = Babyl("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 2
    assert email2dict(test_email1) == email2dict(msgs[0])
    assert email2dict(test_email2) == email2dict(msgs[1])


def test_babyl_send_no_context(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "babyl",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    sender.send(test_email1)
    inbox = Babyl("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    assert email2dict(test_email1) == email2dict(msgs[0])
