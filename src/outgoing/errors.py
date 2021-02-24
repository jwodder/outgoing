import os
from   typing import List, Optional, Sequence
from   .util  import AnyPath

class Error(Exception):
    pass

class InvalidConfigError(Error):
    def __init__(self, details: str, configpath: Optional[AnyPath] = None):
        self.details: str = details
        self.configpath: Optional[AnyPath] = configpath

    def __str__(self) -> str:
        s = ""
        if self.configpath is not None:
            s += f"{os.fsdecode(self.configpath)}: "
        s += f"Invalid configuration: {self.details}"
        return s


class InvalidPasswordError(InvalidConfigError):
    def __str__(self) -> str:
        s = ""
        if self.configpath is not None:
            s += f"{os.fsdecode(self.configpath)}: "
        s += f"Invalid password configuration: {self.details}"
        return s


class MissingConfigError(Error):
    def __init__(self, configpaths: Sequence[AnyPath]):
        self.configpaths: List[AnyPath] = list(configpaths)

    def __str__(self) -> str:
        return (
            "outgoing configuration not found in files: "
            + ", ".join(map(str, self.configpaths))
        )
