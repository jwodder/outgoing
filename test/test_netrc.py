from pathlib import Path
from typing import Optional
import pytest
from outgoing import lookup_netrc
from outgoing.errors import NetrcLookupError


@pytest.mark.parametrize("username", [None, "myname"])
def test_lookup_netrc(
    monkeypatch: pytest.MonkeyPatch, tmp_home: Path, username: Optional[str]
) -> None:
    (tmp_home / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_home / ".netrc").chmod(0o600)
    assert lookup_netrc("api.example.com", username=username) == ("myname", "hunter2")


def test_netrc_username_mismatch(
    monkeypatch: pytest.MonkeyPatch,
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
