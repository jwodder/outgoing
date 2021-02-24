import pathlib
from   typing              import (
    Any, ClassVar, Dict, Optional, TYPE_CHECKING, Tuple, Union, cast
)
import pydantic
from   pydantic.validators import path_validator
from   .                   import core

if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator

    Path = Union[pathlib.Path, str]
    FilePath = Union[pathlib.Path, str]
    DirectoryPath = Union[pathlib.Path, str]

else:
    class Path(pathlib.Path):
        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(format='file-path')

        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_validator
            yield path_expanduser
            yield path_resolve

    class FilePath(pydantic.FilePath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_validator
            yield path_expanduser
            yield path_resolve
            yield from super().__get_validators__()

    class DirectoryPath(pydantic.DirectoryPath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_validator
            yield path_expanduser
            yield path_resolve
            yield from super().__get_validators__()


class PasswordMeta(type):
    def __new__(
        metacls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
    ) -> "PasswordMeta":
        if (
            namespace.get("host") is not None
            and namespace.get("host_field") is not None
        ):
            raise RuntimeError("host and host_field are mutually exclusive")
        if (
            namespace.get("username") is not None
            and namespace.get("username_field") is not None
        ):
            raise RuntimeError("username and username_field are mutually exclusive")
        return cast(PasswordMeta, super().__new__(metacls, name, bases, namespace))


# We have to implement Password configuration via explicit subclassing as using
# a function instead à la pydantic's conlist() leads to mypy errors; cf.
# <https://github.com/samuelcolvin/pydantic/issues/975>
class Password(pydantic.SecretStr, metaclass=PasswordMeta):
    host: ClassVar[Any] = None
    host_field: ClassVar[Optional[str]] = None
    username: ClassVar[Any] = None
    username_field: ClassVar[Optional[str]] = None

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.resolve
        yield from super().__get_validators__()

    @classmethod
    def resolve(cls, v: Any, values: Dict[str, Any]) -> str:
        host = cls.host
        host_field = cls.host_field
        if host_field is not None:
            host = values.get(host_field)
        elif callable(host):
            host = host(values)
        username = cls.username
        username_field = cls.username_field
        if username_field is not None:
            username = values.get(username_field)
        elif callable(username):
            username = username(values)
        return core.resolve_password(
            v,
            host=host,
            username=username,
            configpath=values.get("configpath"),
        )


def path_expanduser(v: pathlib.Path) -> pathlib.Path:
    return v.expanduser()

def path_resolve(v: pathlib.Path, values: Dict[str, Any]) -> pathlib.Path:
    configpath = values.get("configpath")
    if configpath is not None:
        v = pathlib.Path(configpath).parent / v
    return v.resolve()
