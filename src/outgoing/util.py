import os
from pathlib import Path
from typing import Optional, Union

AnyPath = Union[str, bytes, "os.PathLike[str]", "os.PathLike[bytes]"]


def resolve_path(path: AnyPath, basepath: Optional[AnyPath] = None) -> Path:
    p = Path(os.fsdecode(path)).expanduser()
    if basepath is not None:
        p = Path(os.fsdecode(basepath)).parent / p
    return p.resolve()
