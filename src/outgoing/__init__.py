"""
Common interface for multiple e-mail methods

``outgoing`` provides a common interface to multiple different e-mail sending
methods (SMTP, sendmail, mbox, etc.).  Just construct a sender from a
configuration file or object, pass it an ``EmailMessage`` instance, and let the
magical internet daemons take care of the rest.

``outgoing`` itself provides support for only basic sending methods; additional
methods are provided by other packages.

Visit <https://github.com/jwodder/outgoing> or <https://outgoing.rtfd.io> for
more information.
"""

__version__ = "0.6.1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "outgoing@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/outgoing"

from .config import (
    DirectoryPath,
    FilePath,
    NetrcConfig,
    Password,
    Path,
    StandardPassword,
)
from .core import (
    DEFAULT_CONFIG_SECTION,
    Sender,
    from_config_file,
    from_dict,
    get_default_configpath,
    lookup_netrc,
    resolve_password,
)
from .errors import (
    Error,
    InvalidConfigError,
    InvalidPasswordError,
    MissingConfigError,
    NetrcLookupError,
    UnsupportedEmailError,
)
from .util import OpenClosable, resolve_path

__all__ = [
    "DEFAULT_CONFIG_SECTION",
    "DirectoryPath",
    "Error",
    "FilePath",
    "InvalidConfigError",
    "InvalidPasswordError",
    "MissingConfigError",
    "NetrcConfig",
    "NetrcLookupError",
    "OpenClosable",
    "Password",
    "Path",
    "Sender",
    "StandardPassword",
    "UnsupportedEmailError",
    "from_config_file",
    "from_dict",
    "get_default_configpath",
    "lookup_netrc",
    "resolve_password",
    "resolve_path",
]
