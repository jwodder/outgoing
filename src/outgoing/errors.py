import os
from   typing import List, Sequence, Union

class Error(Exception):
    pass

class InvalidConfigError(Error):
    def __init__(self, details: str, configpath: Union[str, os.PathLike, None] = None):
        self.details: str = details
        self.configpath: Union[str, os.PathLike, None] = configpath

    def __str__(self) -> str:
        s = ""
        if self.configpath is not None:
            s += f"{self.configpath}: "
        s += f"Invalid configuration: {self.details}"
        return s


class MissingConfigError(Error):
    def __init__(self, configpaths: Sequence[Union[str, os.PathLike]]):
        self.configpaths: List[Union[str, os.PathLike]] = list(configpaths)

    def __str__(self) -> str:
        return (
            "outgoing configuration not found in files: "
            + ", ".join(map(str, self.configpaths))
        )
