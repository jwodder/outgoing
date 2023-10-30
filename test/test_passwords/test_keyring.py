from pathlib import Path
from shutil import copyfile
import sys
from keyring.backends.null import Keyring as NullKeyring
import pytest
from pytest_mock import MockerFixture
from outgoing import resolve_password
from outgoing.errors import InvalidPasswordError

HUNTER2KEYRING = Path(__file__).resolve().parent.parent / "data" / "Hunter2Keyring.py"

# To disable reading of keyring's config file:
pytestmark = pytest.mark.usefixtures("tmp_home")


def test_keyring_backend(mocker: MockerFixture) -> None:
    m = mocker.patch.object(NullKeyring, "get_password", return_value="hunter2")
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "keyring.backends.null.Keyring",
                }
            }
        )
        == "hunter2"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_host_username_args(mocker: MockerFixture) -> None:
    m = mocker.patch.object(NullKeyring, "get_password", return_value="hunter2")
    assert (
        resolve_password(
            {"keyring": {"backend": "keyring.backends.null.Keyring"}},
            host="api.example.com",
            username="luser",
        )
        == "hunter2"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_host_username_args_overridden(mocker: MockerFixture) -> None:
    m = mocker.patch.object(NullKeyring, "get_password", return_value="hunter2")
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "keyring.backends.null.Keyring",
                }
            },
            host="mx.example.nil",
            username="myself",
        )
        == "hunter2"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_backend_envvar(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")
    m = mocker.patch.object(NullKeyring, "get_password", return_value="hunter2")
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                }
            }
        )
        == "hunter2"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_backend_envvar_override(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyring.backends.fail.Keyring")
    m = mocker.patch.object(NullKeyring, "get_password", return_value="hunter2")
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "keyring.backends.null.Keyring",
                }
            }
        )
        == "hunter2"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_default_backend(mocker: MockerFixture) -> None:
    keyring = mocker.MagicMock(**{"get_password.return_value": "hunter2"})
    get_keyring = mocker.patch("outgoing.passwords.get_keyring", return_value=keyring)
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                }
            }
        )
        == "hunter2"
    )
    get_keyring.assert_called_once_with()
    keyring.get_password.assert_called_once_with("api.example.com", "luser")


def test_keyring_no_password(mocker: MockerFixture) -> None:
    m = mocker.patch.object(NullKeyring, "get_password", return_value=None)
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "keyring.backends.null.Keyring",
                }
            }
        )
    assert (
        str(excinfo.value)
        == "Invalid password configuration: Could not find password for service"
        " 'api.example.com', username 'luser' in keyring"
    )
    m.assert_called_once_with("api.example.com", "luser")


def test_keyring_invalid_spec_type() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"keyring": "keyring.backends.null.Keyring"})
    assert (
        str(excinfo.value)
        == "Invalid password configuration: 'keyring' password specifier must"
        " be an object"
    )


def test_keyring_path() -> None:
    sys_path = list(sys.path)
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "Hunter2Keyring.Keyring",
                    "keyring-path": HUNTER2KEYRING.parent,
                }
            }
        )
        == "hunter2"
    )
    assert sys.path == sys_path


def test_keyring_path_expanduser(tmp_home: Path) -> None:
    (tmp_home / "lib").mkdir()
    copyfile(HUNTER2KEYRING, tmp_home / "lib" / HUNTER2KEYRING.name)
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "Hunter2Keyring.Keyring",
                    "keyring-path": "~/lib",
                }
            }
        )
        == "hunter2"
    )


def test_keyring_path_relative_to_configpath(tmp_path: Path) -> None:
    (tmp_path / "lib").mkdir()
    copyfile(HUNTER2KEYRING, tmp_path / "lib" / HUNTER2KEYRING.name)
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "Hunter2Keyring.Keyring",
                    "keyring-path": "../lib",
                }
            },
            configpath=tmp_path / "foo" / "conf.toml",
        )
        == "hunter2"
    )


def test_keyring_no_service() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"keyring": {"username": "luser"}})
    assert (
        "Invalid password configuration: Invalid 'keyring' password specifier: "
        "1 validation error for KeyringSpec\n"
        "service\n"
        "  Input should be a valid string"
    ) in str(excinfo.value)


def test_keyring_no_username() -> None:
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password({"keyring": {"service": "api.example.com"}})
    assert (
        "Invalid password configuration: Invalid 'keyring' password specifier:"
        " 1 validation error for KeyringSpec\n"
        "username\n"
        "  Input should be a valid string"
    ) in str(excinfo.value)


def test_keyring_nonexistent_keyring_path(tmp_path: Path) -> None:
    keyring_path = tmp_path / "nowhere"
    with pytest.raises(InvalidPasswordError) as excinfo:
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "keyring-path": keyring_path,
                }
            }
        )
    assert (
        "Invalid password configuration: Invalid 'keyring' password specifier:"
        " 1 validation error for KeyringSpec\n"
        "keyring-path\n"
        "  Path does not point to a directory"
    ) in str(excinfo.value)


def test_keyring_path_relative_to_configpath_ignore_spec_configpath(
    tmp_path: Path,
) -> None:
    (tmp_path / "lib").mkdir()
    copyfile(HUNTER2KEYRING, tmp_path / "lib" / HUNTER2KEYRING.name)
    assert (
        resolve_password(
            {
                "keyring": {
                    "service": "api.example.com",
                    "username": "luser",
                    "backend": "Hunter2Keyring.Keyring",
                    "keyring-path": "../lib",
                    "configpath": tmp_path / "bar" / "baz.txt",
                }
            },
            configpath=tmp_path / "foo" / "conf.toml",
        )
        == "hunter2"
    )
