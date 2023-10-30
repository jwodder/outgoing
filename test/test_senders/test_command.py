from __future__ import annotations
from email.message import EmailMessage
import logging
from pathlib import Path
import subprocess
import pytest
from pytest_mock import MockerFixture
from outgoing import Sender, from_dict
from outgoing.senders.command import CommandSender


def test_command_construct_default(tmp_path: Path) -> None:
    sender = from_dict({"method": "command"}, configpath=tmp_path / "foo.toml")
    assert isinstance(sender, Sender)
    assert isinstance(sender, CommandSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.toml",
        "command": ["sendmail", "-i", "-t"],
    }


@pytest.mark.parametrize(
    "command", ["~/my/command --option", ["~/my/command", "--option"]]
)
def test_command_construct(command: str | list[str], tmp_path: Path) -> None:
    sender = from_dict(
        {"method": "command", "command": command}, configpath=tmp_path / "foo.toml"
    )
    assert isinstance(sender, CommandSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.toml",
        "command": command,
    }


@pytest.mark.parametrize(
    "command,shell",
    [
        ("~/my/command --option", True),
        (["~/my/command", "--option"], False),
    ],
)
def test_command_send(
    caplog: pytest.LogCaptureFixture,
    command: str | list[str],
    shell: bool,
    mocker: MockerFixture,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("subprocess.run")
    sender = from_dict(
        {"method": "command", "command": command}, configpath=tmp_path / "foo.toml"
    )
    with sender as s:
        assert sender is s
        sender.send(test_email1)
    m.assert_called_once_with(
        command,
        shell=shell,
        input=bytes(test_email1),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert caplog.record_tuples == [
        (
            "outgoing.senders.command",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via command {command!r}",
        )
    ]


@pytest.mark.parametrize(
    "command,shell",
    [
        ("~/my/command --option", True),
        (["~/my/command", "--option"], False),
    ],
)
def test_command_send_no_context(
    command: str | list[str],
    shell: bool,
    mocker: MockerFixture,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("subprocess.run")
    sender = from_dict(
        {"method": "command", "command": command}, configpath=tmp_path / "foo.toml"
    )
    sender.send(test_email1)
    m.assert_called_once_with(
        command,
        shell=shell,
        input=bytes(test_email1),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
