from pathlib import Path
import subprocess
from typing import List, Union
import pytest
from pytest_mock import MockerFixture
from outgoing import from_dict
from outgoing.senders.command import CommandSender
from testing_lib import test_email1


def test_command_construct_default(tmp_path: Path) -> None:
    sender = from_dict({"method": "command"}, configpath=tmp_path / "foo.toml")
    assert isinstance(sender, CommandSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.toml",
        "command": ["sendmail", "-i", "-t"],
    }


@pytest.mark.parametrize(
    "command", ["~/my/command --option", ["~/my/command", "--option"]]
)
def test_command_construct(command: Union[str, List[str]], tmp_path: Path) -> None:
    sender = from_dict(
        {"method": "command", "command": command}, configpath=tmp_path / "foo.toml"
    )
    assert isinstance(sender, CommandSender)
    assert sender.dict() == {
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
    command: Union[str, List[str]], shell: bool, mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch("subprocess.run")
    sender = from_dict(
        {"method": "command", "command": command}, configpath=tmp_path / "foo.toml"
    )
    with sender:
        sender.send(test_email1)
    m.assert_called_once_with(
        command,
        shell=shell,
        input=bytes(test_email1),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
