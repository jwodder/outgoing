from email.message import EmailMessage
from pathlib import Path
import pytest


@pytest.fixture()
def tmp_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # HOME is used by the netrc module in Python 3.6, even on Windows, so
    # always set it.
    monkeypatch.setenv("HOME", str(tmp_path))
    # At this point, why not always set the Windows var?
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    # Used by platformdirs and keyring:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


@pytest.fixture()
def test_email1() -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Meet me"
    msg["To"] = "my.beloved@love.love"
    msg["From"] = "me@here.qq"
    msg.set_content(
        "Oh my beloved!\n"
        "\n"
        "Wilt thou dine with me on the morrow?\n"
        "\n"
        "We're having hot pockets.\n"
        "\n"
        "Love, Me\n"
    )
    return msg


@pytest.fixture()
def test_email2() -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "No."
    msg["To"] = "me@here.qq"
    msg["From"] = "my.beloved@love.love"
    msg.set_content("Hot pockets?  Thou disgusteth me.\n\nPineapple pizza or RIOT.\n")
    return msg
