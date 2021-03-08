import errno
import os
from pathlib import Path
import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


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
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text(" hunter2\n")
    assert resolve_password({"file": "~/foo.txt"}) == "hunter2"


def test_file_password_expanduser_configpath(
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


def test_file_nonexistent_file(tmp_path: Path) -> None:
    file_path = tmp_path / "nowhere"
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"file": str(file_path)})
    e = FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(file_path))
    assert str(excinfo.value) == (
        f"Invalid password configuration: Invalid 'file' path: {e}"
    )
