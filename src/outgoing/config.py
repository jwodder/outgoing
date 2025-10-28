from __future__ import annotations
from collections.abc import Mapping
import pathlib
from typing import TYPE_CHECKING, Annotated, Any, ClassVar
import pydantic
from pydantic.functional_validators import AfterValidator
from pydantic.types import PathType
from pydantic_core import CoreSchema, core_schema
from . import core
from .errors import InvalidPasswordError
from .util import resolve_path

if TYPE_CHECKING:
    from typing_extensions import Self


def path_resolve(v: pathlib.Path, info: pydantic.ValidationInfo) -> pathlib.Path:
    return resolve_path(v, info.data.get("configpath"))


#: Converts its input to `pathlib.Path` instances, including expanding tildes.
#: If there is a field named ``configpath`` declared before the `Path` field
#: and its value is non-`None`, then the value of the `Path` field will be
#: resolved relative to the parent directory of the ``configpath`` field;
#: otherwise, it will be resolved relative to the current directory.
Path = Annotated[pathlib.Path, AfterValidator(path_resolve)]

#: Like `Path`, but the path must exist and be a file
FilePath = Annotated[pathlib.Path, AfterValidator(path_resolve), PathType("file")]

#: Like `Path`, but the path must exist and be a directory
DirectoryPath = Annotated[pathlib.Path, AfterValidator(path_resolve), PathType("dir")]


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
            def username(values: dict[str, Any]) -> str:
                return "__token__"

    and then use it in your model like so:

    .. code:: python

        class MySender(pydantic.BaseModel):
            configpath: outgoing.Path | None = None
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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, pydantic.SecretStr):
            return self.get_secret_value() == other.get_secret_value()
        else:
            return NotImplemented

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
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: pydantic.GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            cls._resolve, super().__get_pydantic_core_schema__(source_type, handler)
        )

    @classmethod
    def _resolve(cls, v: Any, info: pydantic.ValidationInfo) -> str:
        if not isinstance(v, (str, Mapping)):
            raise ValueError(
                "Password must be either a string or an object with exactly one field"
            )
        if isinstance(cls.host, str):
            try:
                host = info.data[cls.host]
            except KeyError:
                raise ValueError("Insufficient data to determine password")
        elif callable(cls.host):
            try:
                host = cls.host(info.data)
            except Exception:
                raise ValueError("Insufficient data to determine password")
        else:
            assert cls.host is None
            host = None
        if isinstance(cls.username, str):
            try:
                username = info.data[cls.username]
            except KeyError:
                raise ValueError("Insufficient data to determine password")
        elif callable(cls.username):
            try:
                username = cls.username(info.data)
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
                configpath=info.data.get("configpath"),
            )
        except InvalidPasswordError as e:
            raise ValueError(e.details)


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

    configpath: Path | None = None
    netrc: pydantic.StrictBool | FilePath = False
    host: str
    username: str | None = None
    password: StandardPassword | None = None

    @pydantic.model_validator(mode="after")
    def _validate(self) -> Self:
        if self.password is not None:
            if self.netrc:
                raise ValueError("netrc cannot be set when a password is present")
            elif self.username is None:
                raise ValueError("Password cannot be given without username")
        elif self.netrc:
            path: Path | None
            if isinstance(self.netrc, bool):
                path = None
            else:
                path = self.netrc
            try:
                username, password = core.lookup_netrc(
                    self.host, username=self.username, path=path
                )
            except Exception as e:
                raise ValueError(f"Error retrieving password from netrc file: {e}")
            self.username = username
            self.password = StandardPassword(password)
        elif self.username is not None:
            raise ValueError("Username cannot be given without netrc or password")
        return self
