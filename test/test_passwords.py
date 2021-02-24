from   pathlib         import Path
import platform
import pytest
from   outgoing        import resolve_password
from   outgoing.errors import InvalidPasswordError

if platform.system() == "Windows":
    home_var = "USERPROFILE"
else:
    home_var = "HOME"

def test_string_password() -> None:
    assert resolve_password("foo") == "foo"

def test_unknown_provider() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"foo": {}})
    assert str(excinfo.value) == (
        "Invalid password configuration: Unsupported password provider 'foo'"
    )

def test_env_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "bar")
    assert resolve_password({"env": "FOO"}) == "bar"

def test_env_password_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"env": "FOO"})
    assert str(excinfo.value) == (
        "Invalid password configuration: Environment variable 'FOO' not set"
    )

def test_file_password(tmp_path: Path) -> None:
    (tmp_path / "foo.txt").write_text(" hunter2\n")
    assert resolve_password({"file": str(tmp_path / "foo.txt")}) == "hunter2"

def test_file_password_relative(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "foo.txt").write_text(" hunter2\n")
    monkeypatch.chdir(tmp_path)
    assert resolve_password({"file": "foo.txt"}) == "hunter2"

def test_file_password_configpath_relative(tmp_path: Path) -> None:
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / "foo.txt").write_text(" hunter2\n")
    assert resolve_password(
        {"file": "foo.txt"},
        configpath=tmp_path / "bar" / "quux.txt"
    ) == "hunter2"

def test_file_password_expanduser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "foo.txt").write_text(" hunter2\n")
    monkeypatch.setenv(home_var, str(tmp_path))
    assert resolve_password({"file": "~/foo.txt"}) == "hunter2"

def test_file_password_expanduser_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "foo.txt").write_text(" hunter2\n")
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / "foo.txt").write_text("prey3\n")
    monkeypatch.setenv(home_var, str(tmp_path))
    assert resolve_password(
        {"file": "~/foo.txt"},
        configpath=tmp_path / "bar" / "quux.txt",
    ) == "hunter2"

def test_netrc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\n"
        "login myname\n"
        "password hunter2\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    assert resolve_password(
        {"netrc": {}},
        host="api.example.com",
        username="myname",
    ) == "hunter2"

def test_netrc_host_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\n"
        "login myname\n"
        "password hunter2\n"
        "\n"
        "machine mx.egg-sample.nil\n"
        "login myname\n"
        "password 12345\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    assert resolve_password(
        {"netrc": {"host": "mx.egg-sample.nil"}},
        host="api.example.com",
        username="myname",
    ) == "12345"

def test_netrc_username_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\n"
        "login myname\n"
        "password hunter2\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {"netrc": {}},
            host="api.example.com",
            username="myself",
        )
    assert str(excinfo.value) == (
        "Invalid password configuration: Username mismatch in netrc:"
        " config says myself, but netrc says myname"
    )

def test_netrc_host_username_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / ".netrc").write_text(
        "machine api.example.com\n"
        "login myname\n"
        "password hunter2\n"
        "\n"
        "machine mx.egg-sample.nil\n"
        "login myself\n"
        "password 12345\n"
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv(home_var, str(tmp_path))
    assert resolve_password(
        {"netrc": {"host": "mx.egg-sample.nil", "username": "myself"}},
        host="api.example.com",
        username="myname",
    ) == "12345"
