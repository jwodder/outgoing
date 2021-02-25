from pathlib import Path
import platform
from typing import Optional
import pytest
from outgoing import lookup_netrc
from outgoing.errors import NetrcLookupError

if platform.system() == "Windows":
    home_var = "USERPROFILE"
else:
    home_var = "HOME"


@pytest.mark.parametrize("username", [None, "myname"])
def test_lookup_netrc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, username: Optional[str]
) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    assert lookup_netrc("api.example.com", username=username) == ("myname", "hunter2")


def test_netrc_username_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\nlogin myname\npassword hunter2\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    with pytest.raises(NetrcLookupError) as excinfo:
        lookup_netrc("api.example.com", username="myself")
    assert str(excinfo.value) == (
        "Username mismatch in netrc: expected 'myself', but netrc says 'myname'"
    )
