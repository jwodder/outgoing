import pathlib
from typing import Any, ClassVar, Dict, Optional, TYPE_CHECKING, Tuple, Union
import pydantic
from . import core
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
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(format="file-path")

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
      ``host`` argument to `resolve_password()`.

    - Alternatively, `Password` can be subclassed with ``host`` set to a class
      callable (a classmethod or staticmethod), and when that subclass is used
      in a model being instantiated, the callable will be passed a `dict` of
      all validated fields declared before the password field; the return value
      from the callable will then be passed as the ``host`` argument to
      `resolve_password()`.

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

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls._resolve
        yield from super().__get_validators__()

    @classmethod
    def _resolve(cls, v: Any, values: Dict[str, Any]) -> str:
        if isinstance(cls.host, str):
            host = values.get(cls.host)
        elif callable(cls.host):
            host = cls.host(values)
        elif cls.host is None:
            host = None
        else:
            raise RuntimeError("Password.host must be a str, callable, or None")
        if isinstance(cls.username, str):
            username = values.get(cls.username)
        elif callable(cls.username):
            username = cls.username(values)
        elif cls.username is None:
            username = None
        else:
            raise RuntimeError("Password.username must be a str, callable, or None")
        return core.resolve_password(
            v,
            host=host,
            username=username,
            configpath=values.get("configpath"),
        )


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
    fields ``configpath``, ``netrc`` (a boolean or file path; defaults to
    `False`), ``host`` (required), ``username`` (optional), and ``password``
    (optional).

    The model's validators will raise an error if ``password`` is set while
    ``netrc`` is true, or if ``password`` is set but ``username`` is not set.

    The username & password are retrieved from an instance of this class by
    calling the `get_username_password()` method.
    """

    configpath: Optional[Path]
    netrc: Union[pydantic.StrictBool, FilePath] = False
    host: str
    username: Optional[str]
    password: Optional[StandardPassword]

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
        """
        Retrieve the username & password according to the instance's field
        values.

        - If ``netrc`` is false and both ``username`` and ``password`` are
          non-`None`, a ``(username, password)`` pair is returned.

        - If ``netrc`` is false and ``password`` is `None`, return `None`.

        - If ``netrc`` is true or a filepath, look up the entry for ``host`` in
          :file:`~/.netrc` or the given file and return a ``(username,
          password)`` pair.

          - If ``username`` is also non-`None`, raise an error if the username
            in the netrc file differs.

        :raises NetrcLookupError:
            if no entry for ``host`` or the default entry is present in the
            netrc file; or if ``username`` differs from the username in the
            netrc file
        """

        if self.password is not None:
            assert self.username is not None, "Password is set but username is not"
            return (self.username, self.password.get_secret_value())
        elif self.netrc:
            path: Optional[Path]
            if isinstance(self.netrc, bool):
                path = None
            else:
                path = self.netrc
            return core.lookup_netrc(self.host, username=self.username, path=path)
        else:
            return None
