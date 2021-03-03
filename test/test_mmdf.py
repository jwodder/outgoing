from mailbox import MMDF
from pathlib import Path
from email2dict import email2dict
import pytest
from outgoing import from_dict
from outgoing.senders.mailboxes import MMDFSender
from testing_lib import msg_factory, test_email1, test_email2


def test_mmdf_construct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mmdf",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MMDFSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "path": tmp_path / "inbox",
    }
    assert sender._mbox is None


def test_mmdf_send_new_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    sender = from_dict(
        {
            "method": "mmdf",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    inbox = MMDF("inbox", factory=msg_factory)  # type: ignore[arg-type]
    inbox.lock()
    msgs = list(inbox)
    inbox.close()
    assert len(msgs) == 1
    msgdict = email2dict(msgs[0])
    msgdict["unixfrom"] = None
    assert email2dict(test_email1) == msgdict


def test_mmdf_send_extant_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    inbox = MMDF("inbox", factory=msg_factory)  # type: ignore[arg-type]
    inbox.lock()
    inbox.add(test_email1)
    inbox.close()
    sender = from_dict(
        {
            "method": "mmdf",
            "path": "inbox",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    with sender:
        sender.send(test_email2)
    inbox = MMDF("inbox", factory=msg_factory)  # type: ignore[arg-type]
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
