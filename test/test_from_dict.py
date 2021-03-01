from pathlib import Path
import pytest
from outgoing import from_dict
from outgoing.errors import InvalidConfigError
from outgoing.senders.null import NullSender


def test_missing_method() -> None:
    with pytest.raises(InvalidConfigError) as excinfo:
        from_dict({}, configpath="foo.toml")
    assert (
        str(excinfo.value)
        == "foo.toml: Invalid configuration: Required 'method' field not present"
    )


def test_missing_method_no_configpath() -> None:
    with pytest.raises(InvalidConfigError) as excinfo:
        from_dict({})
    assert (
        str(excinfo.value)
        == "Invalid configuration: Required 'method' field not present"
    )


def test_configpath_field(tmp_path: Path) -> None:
    sender = from_dict(
        {"method": "null", "configpath": tmp_path / "bar.toml"},
        configpath=tmp_path / "foo.toml",
    )
    assert isinstance(sender, NullSender)
    assert sender.configpath == tmp_path / "foo.toml"


def test_configpath_field_no_configpath(tmp_path: Path) -> None:
    sender = from_dict({"method": "null", "configpath": tmp_path / "bar.toml"})
    assert isinstance(sender, NullSender)
    assert sender.configpath is None


def test_unknown_method() -> None:
    with pytest.raises(InvalidConfigError) as excinfo:
        from_dict({"method": "foobar"}, configpath="foo.toml")
    assert (
        str(excinfo.value)
        == "foo.toml: Invalid configuration: Unsupported method 'foobar'"
    )


def test_invalid_config() -> None:
    with pytest.raises(
        InvalidConfigError, match=r"^foo\.toml: Invalid configuration: "
    ):
        from_dict({"method": "mbox"}, configpath="foo.toml")
