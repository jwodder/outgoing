from base64 import b64decode
from collections.abc import Mapping
import os
from typing import Any, Optional
from dotenv import dotenv_values
from pydantic import BaseModel
from .config import FilePath, Path
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


def base64_provider(spec: Any) -> str:
    if not isinstance(spec, str):
        raise InvalidPasswordError("'base64' password specifier must be a string")
    try:
        return b64decode(spec, validate=True).decode()
    except Exception as e:
        raise InvalidPasswordError(f"Could not decode base64 password: {e}")


class DotenvSpec(BaseModel):
    configpath: Optional[Path]
    key: str
    file: Optional[FilePath]


def dotenv_provider(spec: Any, configpath: Optional[AnyPath] = None) -> str:
    if not isinstance(spec, Mapping):
        raise InvalidPasswordError("'dotenv' password specifier must be an object")
    ds = DotenvSpec(**{**spec, "configpath": configpath})
    if ds.file is None:
        if configpath is not None:
            ds.file = resolve_path(".env", basepath=configpath)
        else:
            raise InvalidPasswordError("no 'file' or configpath given")
    env = dotenv_values(ds.file)
    try:
        value = env[ds.key]
    except KeyError:
        raise InvalidPasswordError(f"key {ds.key!r} not in {ds.file}")
    else:
        if value is None:
            raise InvalidPasswordError(
                f"key {ds.key!r} in {ds.file} does not have a value"
            )
        return value
