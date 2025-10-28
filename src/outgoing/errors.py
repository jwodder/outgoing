from __future__ import annotations
from collections.abc import Sequence
import os
from .util import AnyPath


class Error(Exception):
    """The superclass for all exceptions raised by ``outgoing``"""

    pass


class InvalidConfigError(Error):
    """Raised on encountering an invalid configuration structure"""

    def __init__(self, details: str, configpath: AnyPath | None = None):
        #: A message about the error
        self.details: str = details
        #: The path to the config file containing the invalid configuration
        self.configpath: AnyPath | None = configpath
        super().__init__(details, configpath)

    def __str__(self) -> str:
        s = ""
        if self.configpath is not None:
            s += f"{os.fsdecode(self.configpath)}: "
        s += f"Invalid configuration: {self.details}"
        return s


class InvalidPasswordError(InvalidConfigError):
    """
    Raised on encountering an invalid password specifier or when no password
    can be determined from a specifier
    """

    def __str__(self) -> str:
        s = ""
        if self.configpath is not None:
            s += f"{os.fsdecode(self.configpath)}: "
        s += f"Invalid password configuration: {self.details}"
        return s


class MissingConfigError(Error):
    """
    Raised when no configuration section can be found in any config files
    """

    def __init__(self, configpaths: Sequence[AnyPath]):
        #: Paths to the configfiles searched for configuration
        self.configpaths: list[AnyPath] = list(configpaths)
        super().__init__(configpaths)

    def __str__(self) -> str:
        return "outgoing configuration not found in files: " + ", ".join(
            map(os.fsdecode, self.configpaths)
        )


class NetrcLookupError(Error):
    """
    Raised by `~outgoing.lookup_netrc()` on failure to find a match in a netrc
    file
    """

    pass


class UnsupportedEmailError(Error):
    """
    Raised by sender objects when asked to send an e-mail that uses features or
    constructs that the sending method does not support
    """

    pass
