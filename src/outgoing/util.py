import os
from pathlib import Path
from typing import Optional, Union

AnyPath = Union[str, bytes, "os.PathLike[str]", "os.PathLike[bytes]"]


def resolve_path(path: AnyPath, configpath: Optional[AnyPath] = None) -> Path:
    p = Path(os.fsdecode(path)).expanduser()
    if configpath is not None:
        p = Path(os.fsdecode(configpath)).parent / p
    return p
