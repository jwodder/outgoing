from base64 import b64decode
from collections.abc import Mapping
from contextlib import ExitStack
import os
import sys
from typing import Any
from dotenv import dotenv_values
from keyring import get_keyring
from keyring.backend import KeyringBackend
from keyring.core import load_keyring
from morecontext import additem
from pydantic import BaseModel, Field, ValidationError
from .config import DirectoryPath, FilePath, Path
from .errors import InvalidPasswordError
from .util import AnyPath, resolve_path


def env_scheme(spec: Any) -> str:
    if not isinstance(spec, str):
        raise InvalidPasswordError("'env' password specifier must be a string")
    try:
        return os.environ[spec]
    except KeyError:
        raise InvalidPasswordError(f"Environment variable {spec!r} not set")


def file_scheme(spec: Any, configpath: AnyPath | None = None) -> str:
    try:
        path = os.fsdecode(spec)
    except Exception:
        raise InvalidPasswordError(
            "'file' password specifier must be a string", configpath=configpath
        )
    filepath = resolve_path(path, configpath)
    try:
        with open(filepath, encoding="utf-8") as fp:
            # Open with open() instead of using filepath.read_text() in order
            # for the error message in PyPy-3.[78] to not include "PosixPath"
            return fp.read().strip()
    except OSError as e:
        raise InvalidPasswordError(f"Invalid 'file' path: {e}", configpath=configpath)


def base64_scheme(spec: Any) -> str:
    if not isinstance(spec, str):
        raise InvalidPasswordError("'base64' password specifier must be a string")
    try:
        return b64decode(spec, validate=True).decode()
    except Exception as e:
        raise InvalidPasswordError(f"Could not decode base64 password: {e}")


class DotenvSpec(BaseModel):
    configpath: Path | None = None
    key: str
    file: FilePath | None = None


def dotenv_scheme(spec: Any, configpath: AnyPath | None = None) -> str:
    if not isinstance(spec, Mapping):
        raise InvalidPasswordError(
            "'dotenv' password specifier must be an object", configpath=configpath
        )
    try:
        ds = DotenvSpec(**{**spec, "configpath": configpath})
    except ValidationError as e:
        raise InvalidPasswordError(
            f"Invalid 'dotenv' password specifier: {e}", configpath=configpath
        )
    if ds.file is None:
        if configpath is not None:
            ds.file = resolve_path(".env", basepath=configpath)
        else:
            raise InvalidPasswordError("no 'file' or configpath given")
    env = dotenv_values(ds.file)
    try:
        value = env[ds.key]
    except KeyError:
        raise InvalidPasswordError(
            f"key {ds.key!r} not in {ds.file}", configpath=configpath
        )
    else:
        if value is None:
            raise InvalidPasswordError(
                f"key {ds.key!r} in {ds.file} does not have a value",
                configpath=configpath,
            )
        return value


class KeyringSpec(BaseModel):
    configpath: Path | None = None
    service: str
    username: str
    backend: str | None = None
    keyring_path: DirectoryPath | None = Field(None, alias="keyring-path")


def keyring_scheme(
    spec: Any,
    host: str | None,
    username: str | None,
    configpath: AnyPath | None = None,
) -> str:
    if not isinstance(spec, Mapping):
        raise InvalidPasswordError(
            "'keyring' password specifier must be an object", configpath=configpath
        )
    try:
        ks = KeyringSpec(
            **{"service": host, "username": username, **spec, "configpath": configpath}
        )
    except ValidationError as e:
        raise InvalidPasswordError(
            f"Invalid 'keyring' password specifier: {e}", configpath=configpath
        )
    with ExitStack() as stack:
        keyring: KeyringBackend
        if ks.backend is not None:
            if ks.keyring_path is not None:
                stack.enter_context(
                    additem(sys.path, str(ks.keyring_path), prepend=True)
                )
            keyring = load_keyring(ks.backend)
            keyring.set_properties_from_env()
        else:
            keyring = get_keyring()
        password = keyring.get_password(ks.service, ks.username)
    if password is None:
        raise InvalidPasswordError(
            f"Could not find password for service {ks.service!r}, username"
            f" {ks.username!r} in keyring",
            configpath=configpath,
        )
    else:
        return password
