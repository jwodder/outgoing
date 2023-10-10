from email.message import EmailMessage
from pathlib import Path
from traceback import format_exception
from click.testing import CliRunner, Result
from mailbits import email2dict
from pytest_mock import MockerFixture
from outgoing.__main__ import main


def show_result(r: Result) -> str:
    if r.exception is not None:
        assert isinstance(r.exc_info, tuple)
        return "".join(format_exception(*r.exc_info))
    else:
        return r.output


def test_main_stdin(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
        r = runner.invoke(
            main,
            ["--config", "cfg.toml"],
            input=bytes(test_email1),
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_args(
    mocker: MockerFixture, test_email1: EmailMessage, test_email2: EmailMessage
) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
        Path("msg1.eml").write_bytes(bytes(test_email1))
        Path("msg2.eml").write_bytes(bytes(test_email2))
        r = runner.invoke(
            main,
            ["--config", "cfg.toml", "msg1.eml", "msg2.eml"],
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 2
    sent1 = instance.send.call_args_list[0][0][0]
    assert isinstance(sent1, EmailMessage)
    assert email2dict(sent1) == email2dict(test_email1)
    sent2 = instance.send.call_args_list[1][0][0]
    assert isinstance(sent2, EmailMessage)
    assert email2dict(sent2) == email2dict(test_email2)


def test_main_custom_section(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text(
            '[outgoing]\nmethod = "command"\n\n[test]\nmethod = "null"\n'
        )
        r = runner.invoke(
            main,
            ["--config", "cfg.toml", "--section", "test"],
            input=bytes(test_email1),
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_no_section(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text(
            'method = "null"\n\n[outgoing]\nmethod = "command"\n'
        )
        r = runner.invoke(
            main,
            ["--config", "cfg.toml", "--no-section"],
            input=bytes(test_email1),
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    m.assert_called_once_with(
        method="null", configpath=Path("cfg.toml"), outgoing={"method": "command"}
    )
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert email2dict(sent) == email2dict(test_email1)


def test_main_default_dotenv(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".env").write_text("DOTENV_PASSWORD=hunter2\n")
        Path("cfg.toml").write_text(
            "[outgoing]\n"
            'method = "smtp"\n'
            'host = "mx.example.com"\n'
            'username = "luser"\n'
            'password = { env = "DOTENV_PASSWORD" }\n'
        )
        r = runner.invoke(
            main,
            ["--config", "cfg.toml"],
            input=bytes(test_email1),
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "hunter2"),
        mocker.call.send_message(mocker.ANY),
        mocker.call.quit(),
    ]


def test_main_custom_dotenv(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".env").write_text("CUSTOM_DOTENV_PASSWORD=12345\n")
        Path("custom.env").write_text("CUSTOM_DOTENV_PASSWORD=hunter2\n")
        Path("cfg.toml").write_text(
            "[outgoing]\n"
            'method = "smtp"\n'
            'host = "mx.example.com"\n'
            'username = "luser"\n'
            'password = { env = "CUSTOM_DOTENV_PASSWORD" }\n'
        )
        r = runner.invoke(
            main,
            ["--config", "cfg.toml", "--env", "custom.env"],
            input=bytes(test_email1),
            standalone_mode=False,
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "hunter2"),
        mocker.call.send_message(mocker.ANY),
        mocker.call.quit(),
    ]
