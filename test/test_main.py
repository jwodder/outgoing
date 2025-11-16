from email.message import EmailMessage
from io import BytesIO
import logging
from pathlib import Path
import sys
from mailbits import email2dict
import pytest
from pytest_mock import MockerFixture
from outgoing import DEFAULT_CONFIG_SECTION, get_default_configpath
from outgoing.__main__ import Command, main


@pytest.mark.parametrize(
    "argv,cmd",
    [
        (
            [],
            Command(
                config=get_default_configpath(),
                env=None,
                log_level=logging.INFO,
                section=DEFAULT_CONFIG_SECTION,
                messages=["-"],
            ),
        ),
        (
            ["--section", "foo"],
            Command(
                config=get_default_configpath(),
                env=None,
                log_level=logging.INFO,
                section="foo",
                messages=["-"],
            ),
        ),
        (
            ["--no-section"],
            Command(
                config=get_default_configpath(),
                env=None,
                log_level=logging.INFO,
                section=None,
                messages=["-"],
            ),
        ),
        (
            ["-l", "DEBUG"],
            Command(
                config=get_default_configpath(),
                env=None,
                log_level=logging.DEBUG,
                section=DEFAULT_CONFIG_SECTION,
                messages=["-"],
            ),
        ),
        (
            ["-l", "debug"],
            Command(
                config=get_default_configpath(),
                env=None,
                log_level=logging.DEBUG,
                section=DEFAULT_CONFIG_SECTION,
                messages=["-"],
            ),
        ),
    ],
)
def test_parse_args(argv: list[str], cmd: Command) -> None:
    assert Command.from_args(argv) == cmd


class MockStdin:
    def __init__(self, content: bytes) -> None:
        self.buffer = BytesIO(content)


def test_main_stdin(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", MockStdin(bytes(test_email1)))
    Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
    assert main(["--config", "cfg.toml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_args(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    test_email2: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    monkeypatch.chdir(tmp_path)
    Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
    Path("msg1.eml").write_bytes(bytes(test_email1))
    Path("msg2.eml").write_bytes(bytes(test_email2))
    assert main(["--config", "cfg.toml", "msg1.eml", "msg2.eml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 2
    sent1 = instance.send.call_args_list[0][0][0]
    assert isinstance(sent1, EmailMessage)
    assert email2dict(sent1) == email2dict(test_email1)
    sent2 = instance.send.call_args_list[1][0][0]
    assert isinstance(sent2, EmailMessage)
    assert email2dict(sent2) == email2dict(test_email2)


def test_main_custom_section(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    monkeypatch.chdir(tmp_path)
    Path("cfg.toml").write_text(
        '[outgoing]\nmethod = "command"\n\n[test]\nmethod = "null"\n'
    )
    Path("msg.eml").write_bytes(bytes(test_email1))
    assert main(["--config", "cfg.toml", "--section", "test", "msg.eml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_no_section(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    monkeypatch.chdir(tmp_path)
    Path("cfg.toml").write_text('method = "null"\n\n[outgoing]\nmethod = "command"\n')
    Path("msg.eml").write_bytes(bytes(test_email1))
    assert main(["--config", "cfg.toml", "--no-section", "msg.eml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    m.assert_called_once_with(
        method="null", configpath=Path("cfg.toml"), outgoing={"method": "command"}
    )
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_default_dotenv(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("DOTENV_PASSWORD=hunter2\n")
    Path("cfg.toml").write_text(
        "[outgoing]\n"
        'method = "smtp"\n'
        'host = "mx.example.com"\n'
        'username = "luser"\n'
        'password = { env = "DOTENV_PASSWORD" }\n'
    )
    Path("msg.eml").write_bytes(bytes(test_email1))
    assert main(["--config", "cfg.toml", "msg.eml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "hunter2"),
        mocker.call.send_message(mocker.ANY),
        mocker.call.quit(),
    ]


def test_main_custom_dotenv(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_email1: EmailMessage,
    tmp_path: Path,
) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("CUSTOM_DOTENV_PASSWORD=12345\n")
    Path("custom.env").write_text("CUSTOM_DOTENV_PASSWORD=hunter2\n")
    Path("cfg.toml").write_text(
        "[outgoing]\n"
        'method = "smtp"\n'
        'host = "mx.example.com"\n'
        'username = "luser"\n'
        'password = { env = "CUSTOM_DOTENV_PASSWORD" }\n'
    )
    Path("msg.eml").write_bytes(bytes(test_email1))
    assert main(["--config", "cfg.toml", "--env", "custom.env", "msg.eml"]) == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "hunter2"),
        mocker.call.send_message(mocker.ANY),
        mocker.call.quit(),
    ]
