from typing import Any
import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


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


@pytest.mark.parametrize("envspec", [["FOO"], {"key": "SECRET"}, 42])
def test_env_password_not_string(envspec: Any) -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"env": envspec})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'env' password specifier must be a string"
    )
