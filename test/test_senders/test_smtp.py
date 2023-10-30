from __future__ import annotations
from email.message import EmailMessage
import logging
from pathlib import Path
import smtplib
from mailbits import email2dict
from pydantic import SecretStr
import pytest
from pytest_mock import MockerFixture
from smtpdfix import AuthController
from outgoing import Sender, from_dict
from outgoing.errors import InvalidConfigError
from outgoing.senders.smtp import SMTPSender

smtpdfix_headers = ["x-mailfrom", "x-peer", "x-rcptto"]


def test_smtp_construct_default_ssl(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MY_PASSWORD", "hunter2")
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "me",
            "password": {"env": "MY_PASSWORD"},
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, Sender)
    assert isinstance(sender, SMTPSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "host": "mx.example.com",
        "username": "me",
        "password": SecretStr("hunter2"),
        "port": 25,
        "ssl": False,
        "netrc": False,
    }
    assert sender._client is None


def test_smtp_construct_no_ssl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_PASSWORD", "hunter2")
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "me",
            "password": {"env": "MY_PASSWORD"},
            "ssl": False,
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, SMTPSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "host": "mx.example.com",
        "username": "me",
        "password": SecretStr("hunter2"),
        "port": 25,
        "ssl": False,
        "netrc": False,
    }
    assert sender._client is None


def test_smtp_construct_ssl(tmp_path: Path) -> None:
    (tmp_path / "secret").write_text("12345\n")
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "me",
            "password": {"file": "secret"},
            "ssl": True,
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, SMTPSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "host": "mx.example.com",
        "username": "me",
        "password": SecretStr("12345"),
        "port": 465,
        "ssl": True,
        "netrc": False,
    }
    assert sender._client is None


def test_smtp_construct_starttls(tmp_path: Path) -> None:
    (tmp_path / "net.rc").write_text(
        "machine mx.example.com\nlogin me\npassword secret\n"
    )
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "netrc": "net.rc",
            "ssl": "starttls",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, SMTPSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "host": "mx.example.com",
        "username": "me",
        "password": SecretStr("secret"),
        "port": 587,
        "ssl": "starttls",
        "netrc": tmp_path / "net.rc",
    }
    assert sender._client is None


@pytest.mark.parametrize("ssl", [False, True, "starttls"])
def test_smtp_construct_explicit_port(ssl: bool | str, tmp_path: Path) -> None:
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "port": 1337,
            "ssl": ssl,
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, SMTPSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.txt",
        "host": "mx.example.com",
        "username": None,
        "password": None,
        "port": 1337,
        "ssl": ssl,
        "netrc": False,
    }


def test_smtp_construct_negative_port(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfigError):
        from_dict(
            {
                "method": "smtp",
                "host": "mx.example.com",
                "port": -1,
            },
            configpath=str(tmp_path / "foo.txt"),
        )


def test_smtp_send_no_ssl_no_auth(
    caplog: pytest.LogCaptureFixture, mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com"})
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 25",
        ),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


def test_smtp_send_no_ssl_auth(
    caplog: pytest.LogCaptureFixture, mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "luser",
            "password": "54321",
        }
    )
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "54321"),
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 25",
        ),
        ("outgoing.senders.smtp", logging.DEBUG, "Logging in as 'luser'"),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


def test_smtp_send_ssl_no_auth(
    caplog: pytest.LogCaptureFixture, mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP_SSL", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com", "ssl": True})
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 465)]
    assert m.return_value.method_calls == [
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 465, using TLS",
        ),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


def test_smtp_send_ssl_auth(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
    test_email1: EmailMessage,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP_SSL", autospec=True)
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "luser",
            "password": "54321",
            "ssl": True,
        }
    )
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 465)]
    assert m.return_value.method_calls == [
        mocker.call.login("luser", "54321"),
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 465, using TLS",
        ),
        ("outgoing.senders.smtp", logging.DEBUG, "Logging in as 'luser'"),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


def test_smtp_send_starttls_no_auth(
    caplog: pytest.LogCaptureFixture, mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com", "ssl": "starttls"})
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 587)]
    assert m.return_value.method_calls == [
        mocker.call.starttls(),
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 587",
        ),
        ("outgoing.senders.smtp", logging.DEBUG, "Enabling STARTTLS"),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


def test_smtp_send_starttls_auth(
    caplog: pytest.LogCaptureFixture, mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing")
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict(
        {
            "method": "smtp",
            "host": "mx.example.com",
            "username": "luser",
            "password": "54321",
            "ssl": "starttls",
        }
    )
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 587)]
    assert m.return_value.method_calls == [
        mocker.call.starttls(),
        mocker.call.login("luser", "54321"),
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]
    assert caplog.record_tuples == [
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Connecting to SMTP server at mx.example.com, port 587",
        ),
        ("outgoing.senders.smtp", logging.DEBUG, "Enabling STARTTLS"),
        ("outgoing.senders.smtp", logging.DEBUG, "Logging in as 'luser'"),
        (
            "outgoing.senders.smtp",
            logging.INFO,
            f"Sending e-mail {test_email1['Subject']!r} via SMTP",
        ),
        (
            "outgoing.senders.smtp",
            logging.DEBUG,
            "Closing connection to mx.example.com",
        ),
    ]


# Spied-on smtplib classes don't work with smtpdfix for some reason (or at
# all?), so we need to split the tests apart.


def test_smtp_fix_send_no_ssl_no_auth(
    smtpd: AuthController, test_email1: EmailMessage
) -> None:
    sender = from_dict({"method": "smtp", "host": smtpd.hostname, "port": smtpd.port})
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


def test_smtp_fix_send_no_ssl_auth(
    smtpd: AuthController, test_email1: EmailMessage
) -> None:
    smtpd.config.enforce_auth = True
    smtpd.config.auth_require_tls = False
    smtpd.config.login_username = "luser"
    smtpd.config.login_password = "hunter2"
    sender = from_dict(
        {
            "method": "smtp",
            "host": smtpd.hostname,
            "port": smtpd.port,
            "username": "luser",
            "password": "hunter2",
        }
    )
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


def test_smtp_fix_send_ssl_no_auth(
    smtpd: AuthController, test_email1: EmailMessage
) -> None:
    smtpd.config.use_ssl = True
    sender = from_dict(
        {"method": "smtp", "host": smtpd.hostname, "port": smtpd.port, "ssl": True}
    )
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


@pytest.mark.skip(reason="Produces PytestUnraisableExceptionWarning on pytest 6.2.3+")
@pytest.mark.xfail(
    raises=smtplib.SMTPNotSupportedError,
    reason="https://github.com/bebleo/smtpdfix/issues/10",
)
def test_smtp_fix_send_ssl_auth(
    smtpd: AuthController,
    test_email1: EmailMessage,
) -> None:
    smtpd.config.enforce_auth = True
    smtpd.config.login_username = "luser"
    smtpd.config.login_password = "hunter2"
    smtpd.config.use_ssl = True
    sender = from_dict(
        {
            "method": "smtp",
            "host": smtpd.hostname,
            "port": smtpd.port,
            "username": "luser",
            "password": "hunter2",
            "ssl": True,
        }
    )
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


def test_smtp_fix_send_starttls_no_auth(
    smtpd: AuthController, test_email1: EmailMessage
) -> None:
    smtpd.config.use_starttls = True
    sender = from_dict(
        {
            "method": "smtp",
            "host": smtpd.hostname,
            "port": smtpd.port,
            "ssl": "starttls",
        }
    )
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


def test_smtp_fix_send_starttls_auth(
    smtpd: AuthController, test_email1: EmailMessage
) -> None:
    smtpd.config.use_starttls = True
    smtpd.config.enforce_auth = True
    smtpd.config.login_username = "luser"
    smtpd.config.login_password = "hunter2"
    sender = from_dict(
        {
            "method": "smtp",
            "host": smtpd.hostname,
            "port": smtpd.port,
            "username": "luser",
            "password": "hunter2",
            "ssl": "starttls",
        }
    )
    with sender:
        sender.send(test_email1)
    assert len(smtpd.messages) == 1
    msgdict = email2dict(smtpd.messages[0])
    for h in smtpdfix_headers:
        msgdict["headers"].pop(h, None)
    assert email2dict(test_email1) == msgdict


def test_smtp_send_no_context(mocker: MockerFixture, test_email1: EmailMessage) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com"})
    sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]


def test_smtp_close_unopened() -> None:
    sender = from_dict({"method": "smtp", "host": "mx.example.com"})
    assert isinstance(sender, SMTPSender)
    with pytest.raises(ValueError) as excinfo:
        sender.close()
    assert str(excinfo.value) == "SMTPSender is not open"
