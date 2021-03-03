from pathlib import Path
import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


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


def test_env_password_not_string() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"env": ["FOO"]})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'env' password specifier must be a string"
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
    assert (
        resolve_password({"file": "foo.txt"}, configpath=tmp_path / "bar" / "quux.txt")
        == "hunter2"
    )


def test_file_password_expanduser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text(" hunter2\n")
    assert resolve_password({"file": "~/foo.txt"}) == "hunter2"


def test_file_password_expanduser_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text(" hunter2\n")
    (tmp_home / "bar").mkdir()
    (tmp_home / "bar" / "foo.txt").write_text("prey3\n")
    assert (
        resolve_password(
            {"file": "~/foo.txt"},
            configpath=tmp_home / "bar" / "quux.txt",
        )
        == "hunter2"
    )


def test_file_password_not_string() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"file": ["foo.txt"]})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'file' password specifier must be a string"
    )


def test_file_password_not_string_configpath() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"file": ["foo.txt"]}, configpath="bar.txt")
    assert str(excinfo.value) == (
        "bar.txt: Invalid password configuration: 'file' password specifier"
        " must be a string"
    )


def test_base64_password() -> None:
    assert resolve_password({"base64": "xaHDqcOn4bmbxJPFpw=="}) == "šéçṛēŧ"


def test_base64_password_not_string() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"base64": 42})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'base64' password specifier must be a string"
    )


@pytest.mark.parametrize(
    "badpass",
    [
        "not&base64",
        "xaHDqcOn4bmbxJPFpw",  # missing characters
        "xaHDqcOn4bmbxJPFpw===",  # extra characters
        "/u36zg==",  # not UTF-8
    ],
)
def test_base64_password_invalid(badpass: str) -> None:
    with pytest.raises(
        InvalidPasswordError,
        match="^Invalid password configuration: Could not decode base64 password: ",
    ):
        resolve_password({"base64": badpass})


def test_dotenv_password(tmp_path: Path) -> None:
    (tmp_path / "foo.txt").write_text("SECRET=hunter2\n")
    assert (
        resolve_password(
            {"dotenv": {"key": "SECRET", "file": str(tmp_path / "foo.txt")}}
        )
        == "hunter2"
    )


def test_dotenv_password_relative(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "foo.txt").write_text("SECRET=hunter2\n")
    monkeypatch.chdir(tmp_path)
    assert (
        resolve_password({"dotenv": {"key": "SECRET", "file": "foo.txt"}}) == "hunter2"
    )


def test_dotenv_password_configpath_relative(tmp_path: Path) -> None:
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / "foo.txt").write_text("SECRET=hunter2\n")
    assert (
        resolve_password(
            {"dotenv": {"key": "SECRET", "file": "foo.txt"}},
            configpath=tmp_path / "bar" / "quux.txt",
        )
        == "hunter2"
    )


def test_dotenv_password_expanduser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text("SECRET=hunter2\n")
    assert (
        resolve_password({"dotenv": {"key": "SECRET", "file": "~/foo.txt"}})
        == "hunter2"
    )


def test_dotenv_password_expanduser_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text("SECRET=hunter2\n")
    (tmp_home / "bar").mkdir()
    (tmp_home / "bar" / "foo.txt").write_text("SECRET=prey3\n")
    assert (
        resolve_password(
            {"dotenv": {"key": "SECRET", "file": "~/foo.txt"}},
            configpath=tmp_home / "bar" / "quux.txt",
        )
        == "hunter2"
    )


def test_dotenv_password_default_configpath(tmp_path: Path) -> None:
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / ".env").write_text("SECRET=hunter2\n")
    assert (
        resolve_password(
            {"dotenv": {"key": "SECRET"}}, configpath=tmp_path / "bar" / "quux.txt"
        )
        == "hunter2"
    )


def test_dotenv_password_default_no_configpath(tmp_path: Path) -> None:
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / ".env").write_text("SECRET=hunter2\n")
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"dotenv": {"key": "SECRET"}})
    assert (
        str(excinfo.value)
        == "Invalid password configuration: no 'file' or configpath given"
    )


def test_dotenv_password_not_in_file(tmp_path: Path) -> None:
    (tmp_path / "foo.txt").write_text("SECRET=hunter2\n")
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {"dotenv": {"key": "HIDDEN", "file": str(tmp_path / "foo.txt")}}
        )
    assert (
        str(excinfo.value)
        == f"Invalid password configuration: key 'HIDDEN' not in {tmp_path/'foo.txt'}"
    )


def test_dotenv_password_no_value(tmp_path: Path) -> None:
    (tmp_path / "foo.txt").write_text("SECRET\n")
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {"dotenv": {"key": "SECRET", "file": str(tmp_path / "foo.txt")}}
        )
    assert (
        str(excinfo.value) == "Invalid password configuration: key 'SECRET' in"
        f" {tmp_path/'foo.txt'} does not have a value"
    )
