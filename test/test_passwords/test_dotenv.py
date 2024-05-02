from pathlib import Path
import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


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
    tmp_home: Path,
) -> None:
    (tmp_home / "foo.txt").write_text("SECRET=hunter2\n")
    assert (
        resolve_password({"dotenv": {"key": "SECRET", "file": "~/foo.txt"}})
        == "hunter2"
    )


def test_dotenv_password_expanduser_configpath(
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
        == f"Invalid password configuration: key 'HIDDEN' not in {tmp_path / 'foo.txt'}"
    )


def test_dotenv_password_no_value(tmp_path: Path) -> None:
    (tmp_path / "foo.txt").write_text("SECRET\n")
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {"dotenv": {"key": "SECRET", "file": str(tmp_path / "foo.txt")}}
        )
    assert (
        str(excinfo.value) == "Invalid password configuration: key 'SECRET' in"
        f" {tmp_path / 'foo.txt'} does not have a value"
    )


def test_dotenv_invalid_spec_type() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"dotenv": "SECRET"})
    assert (
        str(excinfo.value)
        == "Invalid password configuration: 'dotenv' password specifier must"
        " be an object"
    )


def test_dotenv_no_key() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"dotenv": {}})
    assert (
        "Invalid password configuration: Invalid 'dotenv' password specifier: "
        "1 validation error for DotenvSpec\n"
        "key\n"
        "  Field required"
    ) in str(excinfo.value)


def test_dotenv_nonexistent_file(tmp_path: Path) -> None:
    dotenv_path = tmp_path / "nowhere"
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"dotenv": {"key": "SECRET", "file": dotenv_path}})
    assert (
        "Invalid password configuration: Invalid 'dotenv' password specifier:"
        " 1 validation error for DotenvSpec\n"
        "file\n"
        "  Path does not point to a file"
    ) in str(excinfo.value)


def test_dotenv_password_configpath_relative_ignore_spec_configpath(
    tmp_path: Path,
) -> None:
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / "foo.txt").write_text("SECRET=hunter2\n")
    assert (
        resolve_password(
            {
                "dotenv": {
                    "key": "SECRET",
                    "file": "foo.txt",
                    "configpath": tmp_path / "gnusto" / "cleesh.txt",
                }
            },
            configpath=tmp_path / "bar" / "quux.txt",
        )
        == "hunter2"
    )
