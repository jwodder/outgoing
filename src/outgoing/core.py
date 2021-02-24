from   email.message import EmailMessage
import inspect
import json
import os
from   pathlib       import Path
import sys
from   types         import TracebackType
from   typing        import Any, Dict, Optional, Type, Union, cast
import appdirs
import entrypoints
import toml
from   .errors       import InvalidConfigError, InvalidPasswordError, \
                                MissingConfigError

if sys.version_info[:2] >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

DEFAULT_CONFIG_SECTION = "outgoing"

SENDER_GROUP = "outgoing.senders"

PASSWORD_PROVIDER_GROUP = "outgoing.password_providers"

class Sender(Protocol):
    def send(self, msg: EmailMessage) -> Any:
        ...


class SenderManager(Protocol):
    def __enter__(self) -> Sender:
        ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        ...


def get_default_configpath() -> Path:
    return Path(appdirs.user_config_dir("outgoing", "jwodder"), "outgoing.toml")

def from_config_file(
    path: Union[str, os.PathLike, None] = None,
    section: Optional[str] = DEFAULT_CONFIG_SECTION,
    fallback: bool = True,
) -> SenderManager:
    if path is None:
        configpath = get_default_configpath()
    else:
        configpath = Path(path)
    data: Any
    try:
        if configpath.suffix == ".toml":
            data = toml.load(configpath)
        elif configpath.suffix == ".json":
            with configpath.open("r") as fp:
                data = json.load(fp)
        else:
            raise InvalidConfigError(
                "Unsupported file extension",
                configpath=configpath,
            )
    except FileNotFoundError:
        data = None
    if section is not None:
        if not isinstance(data, dict):
            raise InvalidConfigError(
                "Toplevel structure must be a dict/object",
                configpath=configpath,
            )
        data = data.get(section)
    if data is None:
        if fallback and configpath != get_default_configpath():
            try:
                return from_config_file(fallback=False)
            except MissingConfigError as e:
                e.configpaths.append(configpath)
                raise e
        else:
            raise MissingConfigError([configpath])
    if not isinstance(data, dict):
        raise InvalidConfigError(
            "Toplevel structure must be a dict/object",
            configpath=configpath,
        )
    return from_dict(data, configpath=configpath)

def from_dict(
    data: Dict[str, Any],
    configpath: Union[str, os.PathLike, None] = None,
) -> SenderManager:
    try:
        method = data["method"]
    except KeyError:
        raise InvalidConfigError(
            "Required 'method' field not present",
            configpath=configpath,
        )
    try:
        ep = entrypoints.get_single(SENDER_GROUP, method)
    except entrypoints.NoSuchEntryPoint:
        raise InvalidConfigError(
            f"Unsupported method {method!r}",
            configpath=configpath,
        )
    sender_cls = ep.load()
    try:
        return cast(SenderManager, sender_cls(configpath=configpath, **data))
    except (TypeError, ValueError) as e:
        raise InvalidConfigError(str(e), configpath=configpath)
    except InvalidConfigError as e:
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
        raise InvalidPasswordError(
            "Password must be either a string or an object with exactly one field"
        )
    (provider, spec), = password.items()
    try:
        ep = entrypoints.get_single(PASSWORD_PROVIDER_GROUP, provider)
    except entrypoints.NoSuchEntryPoint:
        raise InvalidPasswordError(
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
        raise InvalidPasswordError(str(e))
