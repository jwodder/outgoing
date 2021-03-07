import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


def test_string_password() -> None:
    assert resolve_password("foo") == "foo"


def test_unknown_scheme() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"foo": {}})
    assert str(excinfo.value) == (
        "Invalid password configuration: Unsupported password scheme 'foo'"
    )


def test_multiple_keys() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"foo": {}, "env": "SECRET"})
    assert str(excinfo.value) == (
        "Invalid password configuration: Password must be either a string or an"
        " object with exactly one field"
    )


def test_invalid_env_configpath() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"env": {"key": "SECRET"}}, configpath="foo.toml")
    assert str(excinfo.value) == (
        "foo.toml: Invalid password configuration: 'env' password specifier"
        " must be a string"
    )
