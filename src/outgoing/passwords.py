import os
from typing import Any, Optional
from . import core
from .errors import InvalidPasswordError
from .util import AnyPath, resolve_path


def env_provider(spec: str) -> str:
    try:
        return os.environ[spec]
    except KeyError:
        raise InvalidPasswordError(f"Environment variable {spec!r} not set")


def file_provider(spec: AnyPath, configpath: Optional[AnyPath] = None) -> str:
    filepath = resolve_path(spec, configpath)
    return filepath.read_text().strip()


def netrc_provider(
    spec: Any,
    host: Optional[str],
    username: Optional[str],
    configpath: Optional[AnyPath] = None,
) -> str:
    if not spec:
        path = None
        spec = {}
    elif isinstance(spec, str):
        path = spec
        spec = {}
    elif isinstance(spec, dict):
        path = spec.get("path")
    else:
        raise InvalidPasswordError("netrc password spec must be a string or object")
    if path is not None and not isinstance(path, (str, bytes, os.PathLike)):
        raise InvalidPasswordError("netrc path must be a string")
    host = spec.get("host", host)
    if host is None:
        raise InvalidPasswordError("No host specified for netrc lookup")
    elif not isinstance(host, str):
        raise InvalidPasswordError("Netrc host must be a string")
    username = spec.get("username", username)
    if not (username is None or isinstance(username, str)):
        raise InvalidPasswordError("Netrc username must be a string")
    return core.lookup_netrc(host, username=username, path=path)[1]
