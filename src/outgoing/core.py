from pathlib import Path
from typing  import Any, Dict, Optional, Union

def resolve_password(
    spec: Union[str, Dict[str, Any]],
    host: Optional[str] = None,
    username: Optional[str] = None,
    configpath: Union[str, Path, None] = None,
) -> str:
    raise NotImplementedError
