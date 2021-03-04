from email.message import EmailMessage
from pathlib import Path
from traceback import format_exception
from click.testing import CliRunner, Result
from email2dict import email2dict
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
