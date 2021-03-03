import os
from typing import Any, Optional
from .errors import InvalidPasswordError
from .util import AnyPath, resolve_path


def env_provider(spec: Any) -> str:
    if not isinstance(spec, str):
        raise InvalidPasswordError("'env' password specifier must be a string")
    try:
        return os.environ[spec]
    except KeyError:
        raise InvalidPasswordError(f"Environment variable {spec!r} not set")


def file_provider(spec: Any, configpath: Optional[AnyPath] = None) -> str:
    try:
        path = os.fsdecode(spec)
    except Exception:
        raise InvalidPasswordError(
            "'file' password specifier must be a string", configpath=configpath
        )
    filepath = resolve_path(path, configpath)
    return filepath.read_text().strip()
