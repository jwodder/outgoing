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


def test_env_password_not_string() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"env": ["FOO"]})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'env' password specifier must be a string"
    )
