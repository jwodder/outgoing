import os.path
import pathlib
from   typing              import Any, Dict, TYPE_CHECKING, Union
import pydantic
from   pydantic.validators import path_validator

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
            yield path_expanduser
            yield path_validator

    class FilePath(pydantic.FilePath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_expanduser
            yield from super().__get_validators__()

    class DirectoryPath(pydantic.DirectoryPath):
        @classmethod
        def __get_validators__(cls) -> 'CallableGenerator':
            yield path_expanduser
            yield from super().__get_validators__()


def path_expanduser(v: Any) -> str:
    return os.path.expanduser(v)
