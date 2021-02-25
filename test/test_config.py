import pathlib
from typing import Any, Dict, Optional
from unittest.mock import sentinel
from pydantic import BaseModel, SecretStr, ValidationError
import pytest
from pytest_mock import MockerFixture
from outgoing.config import DirectoryPath, FilePath, Password, Path


class Paths(BaseModel):
    path: Optional[Path]
    filepath: Optional[FilePath]
    dirpath: Optional[DirectoryPath]


def test_path_expanduser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_home: pathlib.Path,
) -> None:
    (tmp_home / "foo").mkdir()
    (tmp_home / "foo" / "bar.txt").touch()
    obj = Paths(path="~/nowhere", filepath="~/foo/bar.txt", dirpath="~/foo")
    assert obj.path == tmp_home / "nowhere"
    assert obj.filepath == tmp_home / "foo" / "bar.txt"
    assert obj.dirpath == tmp_home / "foo"


def test_path_default_none() -> None:
    obj = Paths()
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None


def test_path_explicit_none() -> None:
    obj = Paths(path=None, filepath=None, dirpath=None)
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None


def test_filepath_not_exists(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValidationError):
        Paths(filepath=tmp_path / "nowhere")


def test_dirpath_not_exists(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValidationError):
        Paths(dirpath=tmp_path / "nowhere")


def test_filepath_not_file(tmp_path: pathlib.Path) -> None:
    (tmp_path / "foo").mkdir()
    with pytest.raises(ValidationError):
        Paths(filepath=tmp_path / "foo")


def test_dirpath_not_directory(tmp_path: pathlib.Path) -> None:
    (tmp_path / "foo").touch()
    with pytest.raises(ValidationError):
        Paths(dirpath=tmp_path / "foo")


class ResolvingPaths(BaseModel):
    configpath: Optional[Path]
    path: Path
    filepath: FilePath
    dirpath: DirectoryPath


def test_path_resolve_to_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "bar" / "foo").mkdir(parents=True)
    (tmp_path / "bar" / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath="bar/quux.txt",
        path="nowhere",
        filepath="foo/bar.txt",
        dirpath="foo",
    )
    assert obj.configpath == tmp_path / "bar" / "quux.txt"
    assert obj.path == tmp_path / "bar" / "nowhere"
    assert obj.filepath == tmp_path / "bar" / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "bar" / "foo"


def test_path_resolve_to_curdir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath=None,
        path="nowhere",
        filepath="foo/bar.txt",
        dirpath="foo",
    )
    assert obj.configpath is None
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"


class Password01(Password):
    host_field = "host"
    username_field = "username"


class Config01(BaseModel):
    configpath: pathlib.Path
    host: str
    username: str
    password: Password01


def test_password_fetch_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config01(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == pathlib.Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host="example.com",
        username="me",
        configpath=pathlib.Path("foo/bar"),
    )


class Password02(Password):
    host = "api.example.com"
    username = "mylogin"


class Config02(BaseModel):
    configpath: pathlib.Path
    host: str
    username: str
    password: Password02


def test_password_constant_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config02(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == pathlib.Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host="api.example.com",
        username="mylogin",
        configpath=pathlib.Path("foo/bar"),
    )


class Password03(Password):
    @classmethod
    def host(cls, values: Dict[str, Any]) -> str:
        return f"http:{values['host']}"

    @classmethod
    def username(cls, values: Dict[str, Any]) -> str:
        return f"{values['username']}@{values['host']}"


class Config03(BaseModel):
    configpath: pathlib.Path
    host: str
    username: str
    password: Password03


def test_password_callable_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config03(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == pathlib.Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host="http:example.com",
        username="me@example.com",
        configpath=pathlib.Path("foo/bar"),
    )


def test_password_host_and_host_field() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type(
            "PasswordTest",
            (Password,),
            {"host": "api.example.com", "host_field": "host"},
        )
    assert str(excinfo.value) == "host and host_field are mutually exclusive"


def test_password_username_and_username_field() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type(
            "PasswordTest",
            (Password,),
            {"username": "me", "username_field": "username"},
        )
    assert str(excinfo.value) == "username and username_field are mutually exclusive"
