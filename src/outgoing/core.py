from __future__ import annotations
from collections.abc import Mapping
from email.message import EmailMessage
import inspect
import json
from netrc import netrc
import os
from pathlib import Path
import sys
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, cast
from platformdirs import user_config_path
from . import errors
from .util import AnyPath

if sys.version_info[:2] >= (3, 11):
    from tomllib import load as toml_load
else:
    from tomli import load as toml_load

if sys.version_info[:2] >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

if sys.version_info[:2] >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

if TYPE_CHECKING:
    from typing_extensions import Self

DEFAULT_CONFIG_SECTION = "outgoing"

SENDER_GROUP = "outgoing.senders"

PASSWORD_SCHEME_GROUP = "outgoing.password_schemes"


@runtime_checkable
class Sender(Protocol):
    """
    `Sender` is a `~typing.Protocol` implemented by sender objects.  The
    protocol requires the following behavior:

    - Sender objects can be used as context managers, and their ``__enter__``
      methods return ``self``.

    - Within its own context, calling a sender's ``send(msg:
      email.message.EmailMessage)`` method sends the given e-mail.
    """

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...

    def send(self, msg: EmailMessage) -> Any:
        """Send ``msg`` or raise an exception if that's not possible"""
        ...


def get_default_configpath() -> Path:
    """
    Returns the location of the default config file (regardless of whether it
    exists) as a `pathlib.Path` object
    """
    return user_config_path("outgoing", "jwodder") / "outgoing.toml"


def from_config_file(
    path: Optional[AnyPath] = None,
    section: Optional[str] = DEFAULT_CONFIG_SECTION,
    fallback: bool = True,
) -> Sender:
    """
    Read configuration from the table/field ``section`` (default
    "``outgoing``") in the file at ``path`` (default: the path returned by
    `get_default_configpath()`) and construct a sender object from the
    specification.  The file may be either TOML or JSON (type detected based on
    file extension).  If ``section`` is `None`, the entire file, rather than
    only a single field, is used as the configuration.  If ``fallback`` is
    true, the file is not the default config file, and the file either does not
    exist or does not contain the given section, fall back to reading from the
    default section of the default config file.

    :raises InvalidConfigError: if the configuration is invalid
    :raises MissingConfigError: if no configuration file or section is present
    """
    if path is None:
        configpath = get_default_configpath()
    else:
        configpath = Path(os.fsdecode(path))
    data: Any
    try:
        if configpath.suffix == ".toml":
            with configpath.open("rb") as fb:
                data = toml_load(fb)
        elif configpath.suffix == ".json":
            with configpath.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        else:
            raise errors.InvalidConfigError(
                "Unsupported file extension",
                configpath=configpath,
            )
    except FileNotFoundError:
        data = None
    if data is not None and section is not None:
        if not isinstance(data, Mapping):
            raise errors.InvalidConfigError(
                "Top-level structure must be a dict/object",
                configpath=configpath,
            )
        data = data.get(section)
    if data is None:
        if fallback and configpath != get_default_configpath():
            try:
                return from_config_file(fallback=False)
            except errors.MissingConfigError as e:
                e.configpaths.append(configpath)
                raise e
        else:
            raise errors.MissingConfigError([configpath])
    if not isinstance(data, Mapping):
        raise errors.InvalidConfigError(
            "Section must be a dict/object",
            configpath=configpath,
        )
    return from_dict(data, configpath=configpath)


def from_dict(
    data: Mapping[str, Any],
    configpath: Optional[AnyPath] = None,
) -> Sender:
    """
    Construct a sender object using the given ``data`` as the configuration.
    If ``configpath`` is given, any paths in the ``data`` will be resolved
    relative to ``configpath``'s parent directory; otherwise, they will be
    resolved relative to the current directory.

    ``data`` should not contain a ``"configpath"`` key; such an entry will be
    discarded.

    :raises InvalidConfigError: if the configuration is invalid
    """
    try:
        method = data["method"]
    except KeyError:
        raise errors.InvalidConfigError(
            "Required 'method' field not present",
            configpath=configpath,
        )
    if "configpath" in data:
        # TODO: Emit warning
        data = dict(data)
        data.pop("configpath", None)
    try:
        ep, *_ = entry_points(group=SENDER_GROUP, name=method)
    except ValueError:
        raise errors.InvalidConfigError(
            f"Unsupported method {method!r}",
            configpath=configpath,
        )
    sender_cls = ep.load()
    try:
        return cast(Sender, sender_cls(configpath=configpath, **data))
    except (TypeError, ValueError) as e:
        raise errors.InvalidConfigError(str(e), configpath=configpath)
    except errors.InvalidConfigError as e:
        if e.configpath is None:
            e.configpath = configpath
        raise e


def resolve_password(
    password: str | Mapping[str, Any],
    host: Optional[str] = None,
    username: Optional[str] = None,
    configpath: str | Path | None = None,
) -> str:
    """
    Resolve a configuration password value.  If ``password`` is a string, it is
    returned unchanged.  Otherwise, it must be a mapping with exactly one
    element; the key is used as the name of the password scheme, and the value
    is passed to the corresponding function for retrieving the password.

    When resolving a password field in an ``outgoing`` configuration structure,
    the configpath and any host/service or username values from the
    configuration (or host/service/username constants specific to the sending
    method) should be passed into this function so that they can be made
    available to any password scheme functions that need them.

    :raises InvalidPasswordError:
        if ``password`` is invalid or cannot be resolved
    """
    if isinstance(password, str):
        return password
    elif len(password) != 1:
        raise errors.InvalidPasswordError(
            "Password must be either a string or an object with exactly one field"
        )
    ((scheme, spec),) = password.items()
    try:
        ep, *_ = entry_points(group=PASSWORD_SCHEME_GROUP, name=scheme)
    except ValueError:
        raise errors.InvalidPasswordError(
            f"Unsupported password scheme {scheme!r}",
            configpath=configpath,
        )
    scheme_func = ep.load()
    available_kwargs = {
        "host": host,
        "username": username,
        "configpath": configpath,
    }
    kwargs = {}
    sig = inspect.signature(scheme_func)
    for param in sig.parameters.values():
        if (
            param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
            and param.name in available_kwargs
        ):
            kwargs[param.name] = available_kwargs[param.name]
        elif param.kind is param.VAR_KEYWORD:
            kwargs.update(available_kwargs)
    try:
        return cast(str, scheme_func(spec=spec, **kwargs))
    except (TypeError, ValueError) as e:
        raise errors.InvalidPasswordError(str(e), configpath=configpath)
    except errors.InvalidPasswordError as e:
        if e.configpath is None:
            e.configpath = configpath
        raise e


def lookup_netrc(
    host: str, username: Optional[str] = None, path: Optional[AnyPath] = None
) -> tuple[str, str]:
    """
    Look up the entry for ``host`` in the netrc file at ``path`` (default:
    :file:`~/.netrc`) and return a pair of the username & password.  If
    ``username`` is specified and it does not equal the username in the file, a
    `NetrcLookupError` is raised.

    :raises NetrcLookupError:
        if no entry for ``host`` or the default entry is present in the netrc
        file; or if ``username`` differs from the username in the netrc file
    :raises netrc.NetrcParseError: if the `netrc` module encounters an error
    """
    if path is None:
        rc = netrc()
    else:
        rc = netrc(os.fsdecode(path))
    auth = rc.authenticators(host)
    if auth is None:
        raise errors.NetrcLookupError(
            f"No entry for {host!r} or default found in netrc file"
        )
    elif username not in (None, "") and auth[0] != username:
        raise errors.NetrcLookupError(
            f"Username mismatch in netrc: expected {username!r},"
            f" but netrc says {auth[0]!r}"
        )
    password = auth[2]
    if password in (None, ""):
        raise errors.NetrcLookupError("No password given in netrc entry")
    assert password is not None
    return (auth[0], password)
