from netrc import NetrcParseError
from pathlib import Path
import sys
import pytest
from outgoing import lookup_netrc
from outgoing.errors import NetrcLookupError


@pytest.mark.parametrize("username", [None, "myname"])
def test_lookup_netrc(tmp_home: Path, username: str | None) -> None:
    (tmp_home / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_home / ".netrc").chmod(0o600)
    assert lookup_netrc("api.example.com", username=username) == ("myname", "hunter2")


def test_lookup_netrc_username_mismatch(
    tmp_home: Path,
) -> None:
    (tmp_home / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_home / ".netrc").chmod(0o600)
    with pytest.raises(NetrcLookupError) as excinfo:
        lookup_netrc("api.example.com", username="myself")
    assert str(excinfo.value) == (
        "Username mismatch in netrc: expected 'myself', but netrc says 'myname'"
    )


@pytest.mark.parametrize("username", [None, "yourname"])
def test_lookup_netrc_path(tmp_home: Path, username: str | None) -> None:
    (tmp_home / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_home / ".netrc").chmod(0o600)
    (tmp_home / "net.rc").write_text(
        "machine api.example.com\nlogin yourname\npassword 12345\n"
    )
    assert lookup_netrc(
        "api.example.com", username=username, path=tmp_home / "net.rc"
    ) == ("yourname", "12345")


@pytest.mark.parametrize("username", [None, "myname"])
def test_lookup_netrc_no_match(tmp_home: Path, username: str | None) -> None:
    (tmp_home / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_home / ".netrc").chmod(0o600)
    with pytest.raises(NetrcLookupError) as excinfo:
        lookup_netrc("mx.egg-sample.nil", username=username)
    assert (
        str(excinfo.value)
        == "No entry for 'mx.egg-sample.nil' or default found in netrc file"
    )


@pytest.mark.xfail(
    sys.version_info[:2] < (3, 11),
    reason="Only happens on Python 3.11+",
    raises=NetrcParseError,
)
@pytest.mark.parametrize("username", [None, "myname"])
def test_lookup_netrc_no_password(tmp_home: Path, username: str | None) -> None:
    (tmp_home / ".netrc").write_text("machine api.example.com\nlogin myname\n")
    (tmp_home / ".netrc").chmod(0o600)
    with pytest.raises(NetrcLookupError) as excinfo:
        lookup_netrc("api.example.com", username=username)
    assert str(excinfo.value) == "No password given in netrc entry"
