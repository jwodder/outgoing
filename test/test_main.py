from email.message import EmailMessage
from pathlib import Path
from traceback import format_exception
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture
from outgoing.__main__ import main

BODY1 = (
    "Oh my beloved!\n"
    "\n"
    "Wilt thou dine with me on the morrow?\n"
    "\n"
    "We're having hot pockets.\n"
    "\n"
    "Love, Me\n"
)

msg1 = EmailMessage()
msg1["Subject"] = "Meet me"
msg1["To"] = "my.beloved@love.love"
msg1["From"] = "me@here.qq"
msg1.set_content(BODY1)

BODY2 = "Hot pockets?  Thou disgusteth me.\n\nPineapple pizza or RIOT.\n"

msg2 = EmailMessage()
msg2["Subject"] = "No."
msg2["To"] = "me@here.qq"
msg2["From"] = "my.beloved@love.love"
msg2.set_content(BODY2)


def show_result(r: Result) -> str:
    if r.exception is not None:
        assert isinstance(r.exc_info, tuple)
        return "".join(format_exception(*r.exc_info))
    else:
        return r.output


def test_main_stdin(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
        r = runner.invoke(
            main, ["--config", "cfg.toml"], input=bytes(msg1), standalone_mode=False
        )
    assert r.exit_code == 0, show_result(r)
    assert r.output == ""
    m.assert_called_once_with(method="null", configpath=Path("cfg.toml"))
    instance = m.return_value.__enter__.return_value
    assert instance.send.call_count == 1
    sent = instance.send.call_args[0][0]
    assert isinstance(sent, EmailMessage)
    assert sent.get_content() == BODY1


def test_main_args(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.senders.null.NullSender", autospec=True)
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cfg.toml").write_text('[outgoing]\nmethod = "null"\n')
        Path("msg1.eml").write_bytes(bytes(msg1))
        Path("msg2.eml").write_bytes(bytes(msg2))
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
    assert sent1.get_content() == BODY1
    sent2 = instance.send.call_args_list[1][0][0]
    assert isinstance(sent2, EmailMessage)
    assert sent2.get_content() == BODY2
