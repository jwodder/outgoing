import os
from typing import Optional
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
