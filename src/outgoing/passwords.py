from   netrc   import netrc
import os
from   pathlib import Path
from   typing  import Any, Optional, Union
from   .errors import InvalidPasswordError

def env_provider(spec: str) -> str:
    try:
        return os.environ[spec]
    except KeyError:
        raise InvalidPasswordError(f"Environment variable {spec!r} not set")

def file_provider(spec: str, configpath: Union[str, os.PathLike, None] = None) -> str:
    filepath = Path(spec).expanduser()
    if configpath is not None:
        filepath = Path(configpath, filepath)
    return filepath.read_text().strip()

def netrc_provider(
    spec: Any,
    host: Optional[str],
    username: Optional[str],
    configpath: Union[str, os.PathLike, None] = None,
) -> str:
    if not spec:
        spec = {}
        rc = netrc()
    elif isinstance(spec, str):
        spec = {}
        rc = netrc(spec)
    elif isinstance(spec, dict):
        path = spec.get("path")
        if path is None:
            rc = netrc()
        elif not isinstance(path, str):
            raise InvalidPasswordError("netrc path must be a string")
        else:
            rc = netrc(path)
    else:
        raise InvalidPasswordError("netrc password spec must be a string or object")
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
        raise InvalidPasswordError(
            "No matching or default entry found in netrc file"
        )
    elif username is not None and auth[0] != username:
        raise InvalidPasswordError(
            f"Username mismatch; config says {username}, but netrc says {auth[0]}"
        )
    elif auth[2] is None:
        raise InvalidPasswordError("No password given in netrc entry")
    return auth[2]
