import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


def test_string_password() -> None:
    assert resolve_password("foo") == "foo"


def test_unknown_provider() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"foo": {}})
    assert str(excinfo.value) == (
        "Invalid password configuration: Unsupported password provider 'foo'"
    )
