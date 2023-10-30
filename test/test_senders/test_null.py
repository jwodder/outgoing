from email.message import EmailMessage
import logging
from pathlib import Path
import pytest
from outgoing import Sender, from_dict
from outgoing.senders.null import NullSender


def test_null_construct(tmp_path: Path) -> None:
    sender = from_dict({"method": "null"}, configpath=tmp_path / "foo.toml")
    assert isinstance(sender, Sender)
    assert isinstance(sender, NullSender)
    assert sender.model_dump() == {"configpath": tmp_path / "foo.toml"}


def test_null_send(caplog: pytest.LogCaptureFixture, test_email1: EmailMessage) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    sender = from_dict({"method": "null"})
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    assert caplog.record_tuples == [
        (
            "outgoing.senders.null",
            logging.INFO,
            f"Discarding e-mail {test_email1['Subject']!r}",
        )
    ]


def test_null_send_no_context(test_email1: EmailMessage) -> None:
    sender = from_dict({"method": "null"})
    sender.send(test_email1)
