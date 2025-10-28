from __future__ import annotations
from pathlib import Path
from typing import Any
from pydantic import BaseModel, SecretStr, ValidationError
import pytest
from pytest_mock import MockerFixture
from outgoing.config import Password, StandardPassword


class Config01(BaseModel):
    configpath: Path
    host: str
    username: str
    password: StandardPassword


def test_standard_password(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config01(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password="sentinel",
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host="example.com",
        username="me",
        configpath=Path("foo/bar"),
    )


@pytest.mark.parametrize("badpass", [42, ["SECRET"], True])
def test_standard_password_invalid_type(badpass: Any, mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    with pytest.raises(ValidationError) as excinfo:
        Config01(
            configpath="foo/bar",
            host="example.com",
            username="me",
            password=badpass,
        )
    assert (
        "Password must be either a string or an object with exactly one field"
        in str(excinfo.value)
    )
    m.assert_not_called()


def test_standard_password_invalid_env() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Config01(
            configpath="foo/bar",
            host="example.com",
            username="me",
            password={"env": {"key": "SECRET"}},
        )
    assert "'env' password specifier must be a string" in str(excinfo.value)
    assert "foo/bar" not in str(excinfo.value)


def test_standard_password_invalid_host(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    with pytest.raises(ValidationError) as excinfo:
        Config01(
            configpath="foo/bar",
            host=[42],
            username="me",
            password="sentinel",
        )
    assert "Insufficient data to determine password" in str(excinfo.value)
    m.assert_not_called()


def test_standard_password_invalid_username(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    with pytest.raises(ValidationError) as excinfo:
        Config01(
            configpath="foo/bar",
            host="example.com",
            username=[42],
            password="sentinel",
        )
    assert "Insufficient data to determine password" in str(excinfo.value)
    m.assert_not_called()


class Password02(Password):
    @classmethod
    def host(cls, _values: dict[str, Any]) -> str:
        return "api.example.com"

    @classmethod
    def username(cls, _values: dict[str, Any]) -> str:
        return "mylogin"


class Config02(BaseModel):
    configpath: Path
    host: str
    username: str
    password: Password02


def test_password_constant_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config02(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password="sentinel",
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host="api.example.com",
        username="mylogin",
        configpath=Path("foo/bar"),
    )


class Password03(Password):
    @classmethod
    def host(cls, values: dict[str, Any]) -> str:
        return f"http:{values['host']}"

    @classmethod
    def username(cls, values: dict[str, Any]) -> str:
        return f"{values['username']}@{values['host']}"


class Config03(BaseModel):
    configpath: Path
    host: str
    username: str
    password: Password03


def test_password_callable_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config03(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password="sentinel",
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host="http:example.com",
        username="me@example.com",
        configpath=Path("foo/bar"),
    )


class Config04(BaseModel):
    configpath: Path
    host: str
    username: str
    password: Password


def test_password_unset_fields(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = Config04(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password="sentinel",
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host=None,
        username=None,
        configpath=Path("foo/bar"),
    )


def test_password_bad_host() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type("PasswordTest", (Password,), {"host": 42})
    assert str(excinfo.value) == "Password.host must be a str, callable, or None"


def test_password_bad_username() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type("PasswordTest", (Password,), {"username": 42})
    assert str(excinfo.value) == "Password.username must be a str, callable, or None"


class HostErrorPassword(Password):
    @classmethod
    def host(cls, _values: dict[str, Any]) -> None:
        raise RuntimeError("Invalid host method")


class HostErrorConfig(BaseModel):
    configpath: Path
    password: HostErrorPassword


def test_host_error_password(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    with pytest.raises(ValidationError) as excinfo:
        HostErrorConfig(configpath="foo/bar", password="sentinel")
    assert "Insufficient data to determine password" in str(excinfo.value)
    m.assert_not_called()


class UsernameErrorPassword(Password):
    @classmethod
    def username(cls, _values: dict[str, Any]) -> None:
        raise RuntimeError("Invalid username method")


class UsernameErrorConfig(BaseModel):
    configpath: Path
    password: UsernameErrorPassword


def test_username_error_password(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    with pytest.raises(ValidationError) as excinfo:
        UsernameErrorConfig(configpath="foo/bar", password="sentinel")
    assert "Insufficient data to determine password" in str(excinfo.value)
    m.assert_not_called()


class OptionalPasswordConfig(BaseModel):
    configpath: Path
    host: str
    username: str
    password: StandardPassword | None = None


def test_none_optional_password(mocker: MockerFixture) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    cfg = OptionalPasswordConfig(
        configpath="foo/bar",
        host="example.com",
        username="me",
        password=None,
    )
    assert cfg.model_dump() == {
        "configpath": Path("foo/bar"),
        "host": "example.com",
        "username": "me",
        "password": None,
    }
    m.assert_not_called()
