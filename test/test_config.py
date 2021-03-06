import pathlib
from typing import Any, Dict, Optional, Union
from unittest.mock import sentinel
from pydantic import BaseModel, SecretStr, ValidationError
import pytest
from pytest_mock import MockerFixture
from outgoing.config import (
    DirectoryPath,
    FilePath,
    NetrcConfig,
    Password,
    Path,
    StandardPassword,
)


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


def test_path_resolve_absolute_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "foo").mkdir(parents=True)
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath="bar/quux.txt",
        path=tmp_path / "nowhere",
        filepath=tmp_path / "foo" / "bar.txt",
        dirpath=tmp_path / "foo",
    )
    assert obj.configpath == tmp_path / "bar" / "quux.txt"
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"


class Config01(BaseModel):
    configpath: pathlib.Path
    host: str
    username: str
    password: StandardPassword


def test_standard_password(mocker: MockerFixture) -> None:
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
    @classmethod
    def host(cls, values: Dict[str, Any]) -> str:
        return "api.example.com"

    @classmethod
    def username(cls, values: Dict[str, Any]) -> str:
        return "mylogin"


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


def test_netrc_config(mocker: MockerFixture) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    cfg = NetrcConfig(
        netrc=True,
        host="api.example.com",
        username="myname",
    )
    assert cfg.get_username_password() == (sentinel.USERNAME, sentinel.PASSWORD)
    m.assert_called_once_with("api.example.com", username="myname", path=None)


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    username: Optional[str],
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    (tmp_path / "foo.txt").touch()
    monkeypatch.chdir(tmp_path)
    cfg = NetrcConfig(
        netrc="foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.get_username_password() == (sentinel.USERNAME, sentinel.PASSWORD)
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_path / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path_expanduser(
    mocker: MockerFixture, tmp_home: pathlib.Path, username: Optional[str]
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    (tmp_home / "foo.txt").touch()
    cfg = NetrcConfig(
        netrc="~/foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.get_username_password() == (sentinel.USERNAME, sentinel.PASSWORD)
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_home / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path_configpath(
    mocker: MockerFixture, tmp_path: pathlib.Path, username: Optional[str]
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    (tmp_path / "foo.txt").touch()
    cfg = NetrcConfig(
        configpath=tmp_path / "quux.txt",
        netrc="foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.get_username_password() == (sentinel.USERNAME, sentinel.PASSWORD)
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_path / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_no_such_path(
    mocker: MockerFixture, tmp_path: pathlib.Path, username: Optional[str]
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    with pytest.raises(ValidationError):
        NetrcConfig(
            netrc=tmp_path / "foo.txt",
            host="api.example.com",
            username=username,
        )
    m.assert_not_called()


def test_netrc_config_password_no_username(mocker: MockerFixture) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    with pytest.raises(ValidationError) as excinfo:
        NetrcConfig(
            netrc=False,
            host="api.example.com",
            username=None,
            password="12345",
        )
    assert "Password cannot be given without username" in str(excinfo.value)
    m.assert_not_called()


@pytest.mark.parametrize("netrc", [True, "foo.txt"])
def test_netrc_config_password_netrc(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    netrc: Union[bool, str],
    tmp_path: pathlib.Path,
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    (tmp_path / "foo.txt").touch()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValidationError) as excinfo:
        NetrcConfig(
            netrc=netrc,
            host="api.example.com",
            username="myname",
            password="12345",
        )
    assert "netrc cannot be set when a password is present" in str(excinfo.value)
    m.assert_not_called()


def test_netrc_config_no_netrc(mocker: MockerFixture) -> None:
    m1 = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    m2 = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    cfg = NetrcConfig(
        configpath="foo/bar",
        netrc=False,
        host="api.example.com",
        username="myname",
        password=sentinel.PASSWORD,
    )
    assert cfg.password == SecretStr("12345")
    assert cfg.get_username_password() == ("myname", "12345")
    m1.assert_called_once_with(
        sentinel.PASSWORD,
        host="api.example.com",
        username="myname",
        configpath=pathlib.Path("foo/bar").resolve(),
    )
    m2.assert_not_called()


def test_netrc_config_no_netrc_key(mocker: MockerFixture) -> None:
    m1 = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    m2 = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    cfg = NetrcConfig(
        configpath="foo/bar",
        host="api.example.com",
        username="myname",
        password=sentinel.PASSWORD,
    )
    assert cfg.password == SecretStr("12345")
    assert cfg.get_username_password() == ("myname", "12345")
    m1.assert_called_once_with(
        sentinel.PASSWORD,
        host="api.example.com",
        username="myname",
        configpath=pathlib.Path("foo/bar").resolve(),
    )
    m2.assert_not_called()


def test_netrc_config_nothing(mocker: MockerFixture) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    cfg = NetrcConfig(
        configpath="foo/bar",
        netrc=False,
        host="api.example.com",
        username=None,
        password=None,
    )
    assert cfg.password is None
    assert cfg.get_username_password() is None
    m.assert_not_called()


def test_netrc_config_nothing_no_keys(mocker: MockerFixture) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=(sentinel.USERNAME, sentinel.PASSWORD),
    )
    cfg = NetrcConfig(
        configpath="foo/bar",
        host="api.example.com",
    )
    assert cfg.password is None
    assert cfg.get_username_password() is None
    m.assert_not_called()
