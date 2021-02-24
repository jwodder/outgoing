import pathlib
from   typing              import Any, ClassVar, Dict, Optional, TYPE_CHECKING, Union
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

    class FilePath(pydantic.FilePath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_validator
            yield path_expanduser
            yield from super().__get_validators__()

    class DirectoryPath(pydantic.DirectoryPath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_validator
            yield path_expanduser
            yield from super().__get_validators__()


class Password(pydantic.SecretStr):
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
        if host is not None and host_field is not None:
            raise RuntimeError("host and host_field are mutually exclusive")
        elif host_field is not None:
            host = values.get(host_field)
        elif callable(host):
            host = host(values)
        username = cls.username
        username_field = cls.username_field
        if username is not None and username_field is not None:
            raise RuntimeError("username and username_field are mutually exclusive")
        elif username_field is not None:
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
