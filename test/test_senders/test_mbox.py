from email.message import EmailMessage
import logging
from mailbox import mbox
from pathlib import Path
from mailbits import email2dict
import pytest
from outgoing import Sender, from_dict
from outgoing.senders.mailboxes import MboxSender


def test_mbox_construct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, Sender)
    assert isinstance(sender, MboxSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
    }
    assert sender._mbox is None


def test_mbox_send_new_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    inbox = mbox("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    msgdict = email2dict(msgs[0])
    msgdict["unixfrom"] = None
    assert email2dict(test_email1) == msgdict
    assert caplog.record_tuples == [
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Opening mbox at {tmp_path / 'inbox'}",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.INFO,
            f"Adding e-mail {test_email1['Subject']!r} to mbox at"
            f" {tmp_path / 'inbox'}",
        ),
        (
            "outgoing.senders.mailboxes",
            logging.DEBUG,
            f"Closing mbox at {tmp_path / 'inbox'}",
        ),
    ]


def test_mbox_send_extant_path(
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = mbox("inbox")
    inbox.lock()
    inbox.add(test_email1)
    inbox.close()
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    inbox = mbox("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 2
    msgdict1 = email2dict(msgs[0])
    msgdict1["unixfrom"] = None
    assert email2dict(test_email1) == msgdict1
    msgdict2 = email2dict(msgs[1])
    msgdict2["unixfrom"] = None
    assert email2dict(test_email2) == msgdict2


def test_mbox_send_no_context(
    monkeypatch: pytest.MonkeyPatch, test_email1: EmailMessage, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    sender.send(test_email1)
    inbox = mbox("inbox")
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    msgdict = email2dict(msgs[0])
    msgdict["unixfrom"] = None
    assert email2dict(test_email1) == msgdict


def test_mbox_close_unopened(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mbox",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MboxSender)
    with pytest.raises(ValueError) as excinfo:
        sender.close()
    assert str(excinfo.value) == "Mailbox is not open"
