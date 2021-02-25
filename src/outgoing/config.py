import pathlib
from typing import Any, ClassVar, Dict, Optional, TYPE_CHECKING, Tuple, Union, cast
import pydantic
from . import core
from .util import AnyPath, resolve_path

if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator

    Path = Union[pathlib.Path, str]
    FilePath = Union[pathlib.Path, str]
    DirectoryPath = Union[pathlib.Path, str]

else:

    class Path(pathlib.Path):
        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(format="file-path")

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield path_resolve

    class FilePath(pydantic.FilePath):
        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield path_resolve
            yield from super().__get_validators__()

    class DirectoryPath(pydantic.DirectoryPath):
        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
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
    def __get_validators__(cls) -> "CallableGenerator":
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


def path_resolve(v: AnyPath, values: Dict[str, Any]) -> pathlib.Path:
    return resolve_path(v, values.get("configpath"))


class NetrcPassword(Password):
    host_field = "host"
    username_field = "username"


class NetrcConfig(pydantic.BaseModel):
    configpath: Optional[Path]
    netrc: Union[pydantic.StrictBool, FilePath]
    host: str
    username: Optional[str]
    password: Optional[NetrcPassword]

    @pydantic.root_validator(skip_on_failure=True)
    def _forbid_netrc_if_password(
        cls,  # noqa: B902
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        if values["password"] is not None and values["netrc"]:
            raise ValueError("netrc cannot be set when a password is present")
        return values

    @pydantic.root_validator(skip_on_failure=True)
    def _require_username_if_password(
        cls,  # noqa: B902
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        if values["password"] is not None and values["username"] is None:
            raise ValueError("Password cannot be given without username")
        return values

    def get_username_password(self) -> Optional[Tuple[str, str]]:
        username = self.username
        password = self.password
        if password is not None:
            assert username is not None, "Password is set but username is not"
            return (username, password.get_secret_value())
        elif self.netrc:
            rcpath = self.netrc
            path: Optional[Path]
            if isinstance(rcpath, bool):
                path = None
            else:
                path = rcpath
            return core.lookup_netrc(self.host, username=username, path=path)
        else:
            return None
