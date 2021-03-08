from email.message import EmailMessage
from pathlib import Path
import smtplib
from typing import Union
from email2dict import email2dict
from pydantic import SecretStr
import pytest
from pytest_mock import MockerFixture
from smtpdfix import SMTPDFix
from outgoing import from_dict
from outgoing.errors import InvalidConfigError
from outgoing.senders.smtp import SMTPSender

smtpdfix_headers = ["x-mailfrom", "x-peer", "x-rcptto"]


# See <https://github.com/bebleo/smtpdfix/issues/50> for why this is necessary.
@pytest.fixture
def smtpd_use_ssl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTPD_USE_SSL", "True")


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
    assert isinstance(sender, SMTPSender)
    assert sender.dict() == {
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
    assert sender.dict() == {
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
    assert sender.dict() == {
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
    assert sender.dict() == {
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
def test_smtp_construct_explicit_port(ssl: Union[bool, str], tmp_path: Path) -> None:
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
    assert sender.dict() == {
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
    mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    m = mocker.patch("smtplib.SMTP", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com"})
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 25)]
    assert m.return_value.method_calls == [
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]


def test_smtp_send_no_ssl_auth(
    mocker: MockerFixture, test_email1: EmailMessage
) -> None:
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


def test_smtp_send_ssl_no_auth(
    mocker: MockerFixture, test_email1: EmailMessage
) -> None:
    m = mocker.patch("smtplib.SMTP_SSL", autospec=True)
    sender = from_dict({"method": "smtp", "host": "mx.example.com", "ssl": True})
    with sender:
        sender.send(test_email1)
    assert m.call_args_list == [mocker.call("mx.example.com", 465)]
    assert m.return_value.method_calls == [
        mocker.call.send_message(test_email1),
        mocker.call.quit(),
    ]


def test_smtp_send_ssl_auth(mocker: MockerFixture, test_email1: EmailMessage) -> None:
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


# Spied-on smtplib classes don't work with smtpdfix for some reason (or at
# all?), so we need to split the tests apart.


def test_smtp_fix_send_no_ssl_no_auth(
    smtpd: SMTPDFix, test_email1: EmailMessage
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
    monkeypatch: pytest.MonkeyPatch, smtpd: SMTPDFix, test_email1: EmailMessage
) -> None:
    monkeypatch.setenv("SMTPD_ENFORCE_AUTH", "True")
    monkeypatch.setenv("SMTPD_AUTH_REQUIRE_TLS", "False")
    monkeypatch.setenv("SMTPD_LOGIN_NAME", "luser")
    monkeypatch.setenv("SMTPD_LOGIN_PASSWORD", "hunter2")
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


@pytest.mark.usefixtures("smtpd_use_ssl")
def test_smtp_fix_send_ssl_no_auth(smtpd: SMTPDFix, test_email1: EmailMessage) -> None:
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


@pytest.mark.xfail(
    raises=smtplib.SMTPNotSupportedError,
    reason="https://github.com/bebleo/smtpdfix/issues/10",
)
@pytest.mark.usefixtures("smtpd_use_ssl")
def test_smtp_fix_send_ssl_auth(
    monkeypatch: pytest.MonkeyPatch,
    smtpd: SMTPDFix,
    test_email1: EmailMessage,
) -> None:
    monkeypatch.setenv("SMTPD_ENFORCE_AUTH", "True")
    monkeypatch.setenv("SMTPD_LOGIN_NAME", "luser")
    monkeypatch.setenv("SMTPD_LOGIN_PASSWORD", "hunter2")
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
    monkeypatch: pytest.MonkeyPatch, smtpd: SMTPDFix, test_email1: EmailMessage
) -> None:
    monkeypatch.setenv("SMTPD_USE_STARTTLS", "True")
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
    monkeypatch: pytest.MonkeyPatch, smtpd: SMTPDFix, test_email1: EmailMessage
) -> None:
    monkeypatch.setenv("SMTPD_USE_STARTTLS", "True")
    monkeypatch.setenv("SMTPD_ENFORCE_AUTH", "True")
    monkeypatch.setenv("SMTPD_LOGIN_NAME", "luser")
    monkeypatch.setenv("SMTPD_LOGIN_PASSWORD", "hunter2")
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
