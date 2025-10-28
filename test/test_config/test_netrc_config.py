from __future__ import annotations
from pathlib import Path
from pydantic import SecretStr, ValidationError
import pytest
from pytest_mock import MockerFixture
from outgoing.config import NetrcConfig


def test_netrc_config(mocker: MockerFixture) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=("hunter-the-user", "hunter2"),
    )
    cfg = NetrcConfig(
        netrc=True,
        host="api.example.com",
        username="myname",
    )
    assert cfg.model_dump() == {
        "configpath": None,
        "netrc": True,
        "host": "api.example.com",
        "username": "hunter-the-user",
        "password": SecretStr("hunter2"),
    }
    m.assert_called_once_with("api.example.com", username="myname", path=None)


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    username: str | None,
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=("hunter-the-user", "hunter2"),
    )
    (tmp_path / "foo.txt").touch()
    monkeypatch.chdir(tmp_path)
    cfg = NetrcConfig(
        netrc="foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.model_dump() == {
        "configpath": None,
        "netrc": tmp_path / "foo.txt",
        "host": "api.example.com",
        "username": "hunter-the-user",
        "password": SecretStr("hunter2"),
    }
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_path / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path_expanduser(
    mocker: MockerFixture, tmp_home: Path, username: str | None
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=("hunter-the-user", "hunter2"),
    )
    (tmp_home / "foo.txt").touch()
    cfg = NetrcConfig(
        netrc="~/foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.model_dump() == {
        "configpath": None,
        "netrc": tmp_home / "foo.txt",
        "host": "api.example.com",
        "username": "hunter-the-user",
        "password": SecretStr("hunter2"),
    }
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_home / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_path_configpath(
    mocker: MockerFixture, tmp_path: Path, username: str | None
) -> None:
    m = mocker.patch(
        "outgoing.core.lookup_netrc",
        return_value=("hunter-the-user", "hunter2"),
    )
    (tmp_path / "foo.txt").touch()
    cfg = NetrcConfig(
        configpath=tmp_path / "quux.txt",
        netrc="foo.txt",
        host="api.example.com",
        username=username,
    )
    assert cfg.model_dump() == {
        "configpath": tmp_path / "quux.txt",
        "netrc": tmp_path / "foo.txt",
        "host": "api.example.com",
        "username": "hunter-the-user",
        "password": SecretStr("hunter2"),
    }
    m.assert_called_once_with(
        "api.example.com", username=username, path=tmp_path / "foo.txt"
    )


@pytest.mark.parametrize("username", [None, "myname"])
def test_netrc_config_no_such_path(
    mocker: MockerFixture, tmp_path: Path, username: str | None
) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
    with pytest.raises(ValidationError):
        NetrcConfig(
            netrc=tmp_path / "foo.txt",
            host="api.example.com",
            username=username,
        )
    m.assert_not_called()


def test_netrc_config_password_no_username(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
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
    netrc: bool | str,
    tmp_path: Path,
) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
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


def test_netrc_config_username_no_password_no_netrc(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
    with pytest.raises(ValidationError) as excinfo:
        NetrcConfig(host="api.example.com", username="myname")
    assert "Username cannot be given without netrc or password" in str(excinfo.value)
    m.assert_not_called()


def test_netrc_config_no_netrc(mocker: MockerFixture) -> None:
    m1 = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    m2 = mocker.patch("outgoing.core.lookup_netrc")
    cfg = NetrcConfig(
        configpath="foo/bar",
        netrc=False,
        host="api.example.com",
        username="myname",
        password="sentinel",
    )
    assert cfg.username == "myname"
    assert cfg.password == SecretStr("12345")
    m1.assert_called_once_with(
        "sentinel",
        host="api.example.com",
        username="myname",
        configpath=Path("foo/bar").resolve(),
    )
    m2.assert_not_called()


def test_netrc_config_no_netrc_key(mocker: MockerFixture) -> None:
    m1 = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    m2 = mocker.patch("outgoing.core.lookup_netrc")
    cfg = NetrcConfig(
        configpath="foo/bar",
        host="api.example.com",
        username="myname",
        password="sentinel",
    )
    assert cfg.username == "myname"
    assert cfg.password == SecretStr("12345")
    m1.assert_called_once_with(
        "sentinel",
        host="api.example.com",
        username="myname",
        configpath=Path("foo/bar").resolve(),
    )
    m2.assert_not_called()


def test_netrc_config_nothing(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
    cfg = NetrcConfig(
        configpath="foo/bar",
        netrc=False,
        host="api.example.com",
        username=None,
        password=None,
    )
    assert cfg.username is None
    assert cfg.password is None
    m.assert_not_called()


def test_netrc_config_nothing_no_keys(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.lookup_netrc")
    cfg = NetrcConfig(
        configpath="foo/bar",
        host="api.example.com",
    )
    assert cfg.username is None
    assert cfg.password is None
    m.assert_not_called()


def test_netrc_config_no_entry(tmp_home: Path) -> None:
    (tmp_home / ".netrc").touch()
    with pytest.raises(ValidationError) as excinfo:
        NetrcConfig(host="api.example.com", netrc=True)
    assert (
        "Error retrieving password from netrc file: No entry for"
        " 'api.example.com' or default found in netrc file" in str(excinfo.value)
    )
