from netrc import netrc
import os
from typing import Any, Optional
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
    if path is None:
        rc = netrc()
    elif not isinstance(path, (str, bytes, os.PathLike)):
        raise InvalidPasswordError("netrc path must be a string")
    else:
        rc = netrc(str(resolve_path(path, configpath)))
    host = spec.get("host", host)
    if host is None:
        raise InvalidPasswordError("No host specified for netrc lookup")
    elif not isinstance(host, str):
        raise InvalidPasswordError("Netrc host must be a string")
    username = spec.get("username", username)
    if not (username is None or isinstance(username, str)):
        raise InvalidPasswordError("Netrc username must be a string")
    auth = rc.authenticators(host)
    if auth is None:
        raise InvalidPasswordError("No matching or default entry found in netrc file")
    elif username is not None and auth[0] != username:
        raise InvalidPasswordError(
            f"Username mismatch in netrc: config says {username},"
            f" but netrc says {auth[0]}"
        )
    elif auth[2] is None:
        raise InvalidPasswordError("No password given in netrc entry")
    return auth[2]
