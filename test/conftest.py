from pathlib import Path
import pytest


@pytest.fixture()
def tmp_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # HOME is used by the netrc module in Python 3.6, even on Windows, so
    # always set it.
    monkeypatch.setenv("HOME", str(tmp_path))
    # At this point, why not always set the Windows var?
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path
