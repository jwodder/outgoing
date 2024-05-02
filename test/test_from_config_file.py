import json
from pathlib import Path
import pytest
from outgoing import from_config_file, get_default_configpath
from outgoing.errors import InvalidConfigError, MissingConfigError
from outgoing.senders.mailboxes import MaildirSender, MboxSender


def test_from_default_config_file(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.relative_to(tmp_home)  # Lack of error is pre-3.9's is_relative_to
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    sender = from_config_file()
    assert isinstance(sender, MboxSender)
    assert sender.model_dump() == {
        "configpath": defconf,
        "path": defconf.with_name("inbox"),
    }


def test_from_custom_config_file(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    myconf = tmp_home / "foo.toml"
    myconf.write_text('[outgoing]\nmethod = "maildir"\npath = "dirmail"\n')
    sender = from_config_file(myconf)
    assert isinstance(sender, MaildirSender)
    assert sender.model_dump() == {
        "configpath": myconf,
        "path": tmp_home / "dirmail",
        "folder": None,
    }


def test_from_nonexistent_custom_config_file(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    sender = from_config_file(tmp_home / "foo.toml")
    assert isinstance(sender, MboxSender)
    assert sender.model_dump() == {
        "configpath": defconf,
        "path": defconf.with_name("inbox"),
    }


def test_from_nonexistent_custom_config_file_no_fallback(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(tmp_home / "foo.toml", fallback=False)
    assert (
        str(excinfo.value)
        == f"outgoing configuration not found in files: {tmp_home / 'foo.toml'}"
    )


def test_from_nonexistent_custom_config_file_no_default(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(tmp_home / "foo.toml")
    assert (
        str(excinfo.value) == f"outgoing configuration not found in files: {defconf},"
        f" {tmp_home / 'foo.toml'}"
    )


@pytest.mark.usefixtures("tmp_home")
@pytest.mark.parametrize("fallback", [False, True])
def test_from_nonexistent_default_config_file(fallback: bool) -> None:
    defconf = get_default_configpath()
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(fallback=fallback)
    assert str(excinfo.value) == f"outgoing configuration not found in files: {defconf}"


def test_from_custom_json_config_file(tmp_path: Path) -> None:
    myconf = tmp_path / "foo.json"
    with myconf.open("w") as fp:
        json.dump(
            {
                "outgoing": {
                    "method": "maildir",
                    "path": "dirmail",
                },
            },
            fp,
        )
    sender = from_config_file(myconf)
    assert isinstance(sender, MaildirSender)
    assert sender.model_dump() == {
        "configpath": myconf,
        "path": tmp_path / "dirmail",
        "folder": None,
    }


def test_from_unknown_ext(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfigError) as excinfo:
        from_config_file(tmp_path / "foo.xyz")
    assert (
        str(excinfo.value)
        == f"{tmp_path / 'foo.xyz'}: Invalid configuration: Unsupported file extension"
    )


def test_from_custom_section(tmp_path: Path) -> None:
    (tmp_path / "foo.toml").write_text(
        "[outgoing]\n"
        'method = "mbox"\n'
        'path = "inbox"\n'
        "\n"
        "[sender]\n"
        'method = "maildir"\n'
        'path = "dirmail"\n'
    )
    sender = from_config_file(tmp_path / "foo.toml", section="sender")
    assert isinstance(sender, MaildirSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.toml",
        "path": tmp_path / "dirmail",
        "folder": None,
    }


def test_from_none_section(tmp_path: Path) -> None:
    (tmp_path / "foo.toml").write_text(
        'method = "maildir"\n'
        'path = "dirmail"\n'
        "\n"
        "[outgoing]\n"
        'method = "mbox"\n'
        'path = "inbox"\n'
    )
    sender = from_config_file(tmp_path / "foo.toml", section=None)
    assert isinstance(sender, MaildirSender)
    assert sender.model_dump() == {
        "configpath": tmp_path / "foo.toml",
        "path": tmp_path / "dirmail",
        "folder": None,
    }


def test_from_no_section_custom_config_file(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    (tmp_home / "foo.toml").write_text(
        '[sender]\nmethod = "maildir"\npath = "dirmail"\n'
    )
    sender = from_config_file(tmp_home / "foo.toml")
    assert isinstance(sender, MboxSender)
    assert sender.model_dump() == {
        "configpath": defconf,
        "path": defconf.with_name("inbox"),
    }


def test_from_no_section_custom_config_file_no_fallback(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[outgoing]\nmethod = "mbox"\npath = "inbox"\n')
    (tmp_home / "foo.toml").write_text(
        '[sender]\nmethod = "maildir"\npath = "dirmail"\n'
    )
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(tmp_home / "foo.toml", fallback=False)
    assert (
        str(excinfo.value)
        == f"outgoing configuration not found in files: {tmp_home / 'foo.toml'}"
    )


def test_from_no_section_in_custom_config_file_or_default(tmp_home: Path) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[sender]\nmethod = "mbox"\npath = "inbox"\n')
    (tmp_home / "foo.toml").write_text(
        '[sender]\nmethod = "maildir"\npath = "dirmail"\n'
    )
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(tmp_home / "foo.toml")
    assert (
        str(excinfo.value) == f"outgoing configuration not found in files: {defconf},"
        f" {tmp_home / 'foo.toml'}"
    )


@pytest.mark.usefixtures("tmp_home")
@pytest.mark.parametrize("fallback", [False, True])
def test_from_no_section_default_config_file(fallback: bool) -> None:
    defconf = get_default_configpath()
    defconf.parent.mkdir(parents=True, exist_ok=True)
    defconf.write_text('[sender]\nmethod = "mbox"\npath = "inbox"\n')
    with pytest.raises(MissingConfigError) as excinfo:
        from_config_file(fallback=fallback)
    assert str(excinfo.value) == f"outgoing configuration not found in files: {defconf}"


def test_toplevel_not_dict(tmp_path: Path) -> None:
    myconf = tmp_path / "foo.json"
    with myconf.open("w") as fp:
        json.dump(
            [
                {
                    "outgoing": {
                        "method": "maildir",
                        "path": "dirmail",
                    },
                }
            ],
            fp,
        )
    with pytest.raises(InvalidConfigError) as excinfo:
        from_config_file(myconf)
    assert (
        str(excinfo.value)
        == f"{myconf}: Invalid configuration: Top-level structure must be a dict/object"
    )


def test_section_not_dict(tmp_path: Path) -> None:
    (tmp_path / "foo.toml").write_text(
        '[[outgoing]]\nmethod = "mbox"\npath = "inbox"\n'
    )
    with pytest.raises(InvalidConfigError) as excinfo:
        from_config_file(tmp_path / "foo.toml")
    assert (
        str(excinfo.value)
        == f"{tmp_path / 'foo.toml'}: Invalid configuration: Section must be a"
        " dict/object"
    )
