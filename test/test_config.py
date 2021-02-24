import pathlib
import platform
from   typing          import Optional
from   pydantic        import BaseModel, ValidationError
import pytest
from   outgoing.config import DirectoryPath, FilePath, Path

if platform.system() == "Windows":
    home_var = "USERPROFILE"
else:
    home_var = "HOME"

class Paths(BaseModel):
    path: Optional[Path]
    filepath: Optional[FilePath]
    dirpath: Optional[DirectoryPath]

def test_path_expanduser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.setenv(home_var, str(tmp_path))
    obj = Paths(path="~/nowhere", filepath="~/foo/bar.txt", dirpath="~/foo")
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"

def test_path_default_none() -> None:
    obj = Paths()
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None

def test_path_explicit_none() -> None:
    obj = Paths(path=None, filepath=None, dirpath=None)
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None

def test_filepath_not_exists(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValidationError):
        Paths(filepath=tmp_path / "nowhere")

def test_dirpath_not_exists(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValidationError):
        Paths(dirpath=tmp_path / "nowhere")

def test_filepath_not_file(tmp_path: pathlib.Path) -> None:
    (tmp_path / "foo").mkdir()
    with pytest.raises(ValidationError):
        Paths(filepath=tmp_path / "foo")

def test_dirpath_not_directory(tmp_path: pathlib.Path) -> None:
    (tmp_path / "foo").touch()
    with pytest.raises(ValidationError):
        Paths(dirpath=tmp_path / "foo")
