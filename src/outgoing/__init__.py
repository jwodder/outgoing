"""
Abstract interface for different e-mail methods

Visit <https://github.com/jwodder/outgoing> for more information.
"""

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "outgoing@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/outgoing"

from .core import from_config_file, from_dict, get_default_configpath, resolve_password

__all__ = [
    "from_config_file",
    "from_dict",
    "get_default_configpath",
    "resolve_password",
]
