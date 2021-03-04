import pytest
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError


def test_base64_password() -> None:
    assert resolve_password({"base64": "xaHDqcOn4bmbxJPFpw=="}) == "šéçṛēŧ"


def test_base64_password_not_string() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"base64": 42})
    assert str(excinfo.value) == (
        "Invalid password configuration: 'base64' password specifier must be a string"
    )


@pytest.mark.parametrize(
    "badpass",
    [
        "not&base64",
        "xaHDqcOn4bmbxJPFpw",  # missing characters
        "xaHDqcOn4bmbxJPFpw===",  # extra characters
        "/u36zg==",  # not UTF-8
    ],
)
def test_base64_password_invalid(badpass: str) -> None:
    with pytest.raises(
        InvalidPasswordError,
        match="^Invalid password configuration: Could not decode base64 password: ",
    ):
        resolve_password({"base64": badpass})
