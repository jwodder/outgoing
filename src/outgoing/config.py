from collections.abc import Mapping
import pathlib
from typing import Any, ClassVar, Dict, Optional, TYPE_CHECKING, Union
import pydantic
from . import core
from .errors import InvalidPasswordError
from .util import AnyPath, resolve_path

if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator

    Path = pathlib.Path
    FilePath = pathlib.Path
    DirectoryPath = pathlib.Path

else:

    class Path(pathlib.Path):
        """
        Converts its input to `pathlib.Path` instances, including expanding
        tildes.  If there is a field named ``configpath`` declared before the
        `Path` field and its value is non-`None`, then the value of the `Path`
        field will be resolved relative to the parent directory of the
        ``configpath`` field; otherwise, it will be resolved relative to the
        current directory.
        """

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield path_resolve

    class FilePath(pydantic.FilePath):
        """ Like `Path`, but the path must exist and be a file """

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield path_resolve
            yield from super().__get_validators__()

    class DirectoryPath(pydantic.DirectoryPath):
        """ Like `Path`, but the path must exist and be a directory """

        @classmethod
        def __get_validators__(cls) -> "CallableGenerator":
            yield path_resolve
            yield from super().__get_validators__()


# We have to implement Password configuration via explicit subclassing as using
# a function instead à la pydantic's conlist() leads to mypy errors; cf.
# <https://github.com/samuelcolvin/pydantic/issues/975>
class Password(pydantic.SecretStr):
    """
    A subclass of `pydantic.SecretStr` that accepts ``outgoing`` password
    specifiers as input and automatically resolves them using
    `resolve_password()`.  Host, username, and ``configpath`` values are passed
    to `resolve_password()` as follows:

    - If `Password` is subclassed and given a ``host`` class variable naming a
      field, and if the subclass is then used in a model where a field with
      that name is declared before the `Password` subclass field, then when the
      model is instantiated, the value of the named field will be passed as the
      ``host`` argument to `resolve_password()`.  (If the named field is not
      present on the model that uses the subclass, the `Password` field will
      fail validation.)

    - Alternatively, `Password` can be subclassed with ``host`` set to a class
      callable (a classmethod or staticmethod), and when that subclass is used
      in a model being instantiated, the callable will be passed a `dict` of
      all validated fields declared before the password field; the return value
      from the callable will then be passed as the ``host`` argument to
      `resolve_password()`.  (If the callable raises an exception, the
      `Password` field will fail validation.)

    - If `Password` is used in a model without being subclassed, or if ``host``
      is not defined in a subclass, then `None` will be passed as the ``host``
      argument to `resolve_password()`.

    - The ``username`` argument to `resolve_password()` can likewise be defined
      by subclassing `Password` and defining ``username`` appropriately.

    - If there is a field named ``configpath`` declared before the `Password`
      field, then the value of ``configpath`` is passed to
      `resolve_password()`.

    For example, if writing a pydantic model for a sender configuration where
    the host-analogue value is passed in a field named ``"service"`` and for
    which the username is always ``"__token__"``, you would subclass `Password`
    like this:

    .. code:: python

        class MyPassword(outgoing.Password):
            host = "service"

            @staticmethod
            def username(values: Dict[str, Any]) -> str:
                return "__token__"

    and then use it in your model like so:

    .. code:: python

        class MySender(pydantic.BaseModel):
            configpath: Optional[outgoing.Path]
            service: str
            password: MyPassword  # Must come after `configpath` and `service`!
            # ... other fields ...

    Then, when ``MySender`` is instantiated, the input to the ``password``
    field would be automatically resolved by doing (effectively):

    .. code:: python

        my_sender.password = pydantic.SecretStr(
            resolve_password(
                my_sender.password,
                host=my_sender.service,
                username="__token__",
                configpath=my_sender.configpath,
            )
        )

    .. note::

        As this is a subclass of `pydantic.SecretStr`, the value of a
        `Password` field is retrieved by calling its ``get_secret_value()``
        method.
    """

    host: ClassVar[Any] = None
    username: ClassVar[Any] = None

    def __init_subclass__(cls) -> None:
        if (
            cls.host is not None
            and not isinstance(cls.host, str)
            and not callable(cls.host)
        ):
            raise RuntimeError("Password.host must be a str, callable, or None")
        if (
            cls.username is not None
            and not isinstance(cls.username, str)
            and not callable(cls.username)
        ):
            raise RuntimeError("Password.username must be a str, callable, or None")

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls._resolve
        yield from super().__get_validators__()

    @classmethod
    def _resolve(cls, v: Any, values: Dict[str, Any]) -> str:
        if not isinstance(v, (str, Mapping)):
            raise ValueError(
                "Password must be either a string or an object with exactly one field"
            )
        if isinstance(cls.host, str):
            try:
                host = values[cls.host]
            except KeyError:
                raise ValueError("Insufficient data to determine password")
        elif callable(cls.host):
            try:
                host = cls.host(values)
            except Exception:
                raise ValueError("Insufficient data to determine password")
        else:
            assert cls.host is None
            host = None
        if isinstance(cls.username, str):
            try:
                username = values[cls.username]
            except KeyError:
                raise ValueError("Insufficient data to determine password")
        elif callable(cls.username):
            try:
                username = cls.username(values)
            except Exception:
                raise ValueError("Insufficient data to determine password")
        else:
            assert cls.username is None
            username = None
        try:
            return core.resolve_password(
                v,
                host=host,
                username=username,
                configpath=values.get("configpath"),
            )
        except InvalidPasswordError as e:
            raise ValueError(e.details)


def path_resolve(v: AnyPath, values: Dict[str, Any]) -> pathlib.Path:
    return resolve_path(v, values.get("configpath"))


class StandardPassword(Password):
    """
    A subclass of `Password` in which ``host`` is set to ``"host"`` and
    ``username`` is set to ``"username"``
    """

    host = "host"
    username = "username"


class NetrcConfig(pydantic.BaseModel):
    """
    A pydantic model usable as a base class for any senders that wish to
    support both ``password`` fields and netrc files.  The model accepts the
    fields ``configpath``, ``netrc`` (a boolean or a file path; defaults to
    `False`), ``host`` (required), ``username`` (optional), and ``password``
    (optional).  When the model is instantiated, if ``password`` is `None` but
    ``netrc`` is true or a filepath, the entry for ``host`` is looked up in
    :file:`~/.netrc` or the given file, and the ``username`` and ``password``
    fields are set to the values found.

    The model will raise a validation error if any of the following are true:

    - ``password`` is set but ``netrc`` is true
    - ``password`` is set but ``username`` is not set
    - ``username`` is set but ``password`` is not set and ``netrc`` is false
    - ``netrc`` is true or a filepath, ``username`` is non-`None`, and the
      username in the netrc file differs from ``username``
    - ``netrc`` is true or a filepath and no entry can be found in the netrc
      file
    """

    configpath: Optional[Path]
    netrc: Union[pydantic.StrictBool, FilePath] = False
    host: str
    username: Optional[str]
    password: Optional[StandardPassword]

    @pydantic.root_validator(skip_on_failure=True)
    def _validate(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # noqa: B902, U100
        if values["password"] is not None:
            if values["netrc"]:
                raise ValueError("netrc cannot be set when a password is present")
            elif values["username"] is None:
                raise ValueError("Password cannot be given without username")
        elif values["netrc"]:
            path: Optional[Path]
            if isinstance(values["netrc"], bool):
                path = None
            else:
                path = values["netrc"]
            try:
                username, password = core.lookup_netrc(
                    values["host"], username=values["username"], path=path
                )
            except Exception as e:
                raise ValueError(f"Error retrieving password from netrc file: {e}")
            values["username"] = username
            values["password"] = StandardPassword(password)
        elif values["username"] is not None:
            raise ValueError("Username cannot be given without netrc or password")
        return values
