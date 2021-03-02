from email.message import EmailMessage
import inspect
import json
from netrc import netrc
import os
from pathlib import Path
import sys
from types import TracebackType
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Union, cast
import appdirs
import entrypoints
import toml
from . import errors
from .util import AnyPath

if sys.version_info[:2] >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

DEFAULT_CONFIG_SECTION = "outgoing"

SENDER_GROUP = "outgoing.senders"

PASSWORD_PROVIDER_GROUP = "outgoing.password_providers"

S = TypeVar("S", bound="Sender")


class Sender(Protocol):
    def __enter__(self: S) -> S:
        ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        ...

    def send(self, msg: EmailMessage) -> Any:
        ...


def get_default_configpath() -> Path:
    return Path(appdirs.user_config_dir("outgoing", "jwodder"), "outgoing.toml")


def from_config_file(
    path: Optional[AnyPath] = None,
    section: Optional[str] = DEFAULT_CONFIG_SECTION,
    fallback: bool = True,
) -> Sender:
    if path is None:
        configpath = get_default_configpath()
    else:
        configpath = Path(os.fsdecode(path))
    data: Any
    try:
        if configpath.suffix == ".toml":
            data = toml.load(configpath)
        elif configpath.suffix == ".json":
            with configpath.open("r") as fp:
                data = json.load(fp)
        else:
            raise errors.InvalidConfigError(
                "Unsupported file extension",
                configpath=configpath,
            )
    except FileNotFoundError:
        data = None
    if data is not None and section is not None:
        if not isinstance(data, dict):
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
    if not isinstance(data, dict):
        raise errors.InvalidConfigError(
            "Section must be a dict/object",
            configpath=configpath,
        )
    return from_dict(data, configpath=configpath)


def from_dict(
    data: Dict[str, Any],
    configpath: Optional[AnyPath] = None,
) -> Sender:
    try:
        method = data["method"]
    except KeyError:
        raise errors.InvalidConfigError(
            "Required 'method' field not present",
            configpath=configpath,
        )
    if "configpath" in data:
        # TODO: Emit warning
        data = data.copy()
        data.pop("configpath", None)
    try:
        ep = entrypoints.get_single(SENDER_GROUP, method)
    except entrypoints.NoSuchEntryPoint:
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
    password: Union[str, Dict[str, Any]],
    host: Optional[str] = None,
    username: Optional[str] = None,
    configpath: Union[str, Path, None] = None,
) -> str:
    if isinstance(password, str):
        return password
    elif len(password) != 1:
        raise errors.InvalidPasswordError(
            "Password must be either a string or an object with exactly one field"
        )
    ((provider, spec),) = password.items()
    try:
        ep = entrypoints.get_single(PASSWORD_PROVIDER_GROUP, provider)
    except entrypoints.NoSuchEntryPoint:
        raise errors.InvalidPasswordError(
            f"Unsupported password provider {provider!r}",
            configpath=configpath,
        )
    provider_func = ep.load()
    available_kwargs = {
        "host": host,
        "username": username,
        "configpath": configpath,
    }
    kwargs = {}
    sig = inspect.signature(provider_func)
    for param in sig.parameters.values():
        if (
            param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
            and param.name in available_kwargs
        ):
            kwargs[param.name] = available_kwargs[param.name]
        elif param.kind is param.VAR_KEYWORD:
            kwargs.update(available_kwargs)
    try:
        return cast(str, provider_func(spec=spec, **kwargs))
    except (TypeError, ValueError) as e:
        raise errors.InvalidPasswordError(str(e))


def lookup_netrc(
    host: str, username: Optional[str] = None, path: Optional[AnyPath] = None
) -> Tuple[str, str]:
    if path is None:
        rc = netrc()
    else:
        rc = netrc(os.fsdecode(path))
    auth = rc.authenticators(host)
    if auth is None:
        raise errors.NetrcLookupError(
            f"No entry for {host!r} or default found in netrc file"
        )
    elif username is not None and auth[0] != username:
        raise errors.NetrcLookupError(
            f"Username mismatch in netrc: expected {username!r},"
            f" but netrc says {auth[0]!r}"
        )
    password = auth[2]
    if password is None:
        # mypy says this can happen, but the actual implementation in CPython
        # says otherwise.
        raise errors.NetrcLookupError("No password given in netrc entry")
    return (auth[0], password)
