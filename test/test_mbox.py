from mailbox import mbox
from pathlib import Path
from email2dict import email2dict
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import MboxSender
from testing_lib import msg_factory, test_email1, test_email2


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


def test_mbox_send_new_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
    msgdict = email2dict(msgs[0])
    msgdict["unixfrom"] = None
    assert email2dict(test_email1) == msgdict


def test_mbox_send_extant_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = mbox("inbox", factory=msg_factory)  # type: ignore[arg-type]
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
    inbox = mbox("inbox", factory=msg_factory)  # type: ignore[arg-type]
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
