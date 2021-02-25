from pathlib import Path
import platform
import pytest

if platform.system() == "Windows":
    home_var = "USERPROFILE"
else:
    home_var = "HOME"


@pytest.fixture()
def tmp_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv(home_var, str(tmp_path))
    return tmp_path
