from pathlib import Path
from typing import Any, Dict
from unittest.mock import sentinel
from pydantic import BaseModel, SecretStr
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
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host="example.com",
        username="me",
        configpath=Path("foo/bar"),
    )


class Password02(Password):
    @classmethod
    def host(cls, values: Dict[str, Any]) -> str:
        return "api.example.com"

    @classmethod
    def username(cls, values: Dict[str, Any]) -> str:
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
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host="api.example.com",
        username="mylogin",
        configpath=Path("foo/bar"),
    )


class Password03(Password):
    @classmethod
    def host(cls, values: Dict[str, Any]) -> str:
        return f"http:{values['host']}"

    @classmethod
    def username(cls, values: Dict[str, Any]) -> str:
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
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
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
        password=sentinel.PASSWORD,
    )
    assert cfg.configpath == Path("foo/bar")
    assert cfg.host == "example.com"
    assert cfg.username == "me"
    assert cfg.password == SecretStr("12345")
    m.assert_called_once_with(
        sentinel.PASSWORD,
        host=None,
        username=None,
        configpath=Path("foo/bar"),
    )


def test_password_bad_host(mocker: MockerFixture) -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type("PasswordTest", (Password,), {"host": 42})
    assert str(excinfo.value) == "Password.host must be a str, callable, or None"


def test_password_bad_username(mocker: MockerFixture) -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type("PasswordTest", (Password,), {"username": 42})
    assert str(excinfo.value) == "Password.username must be a str, callable, or None"
