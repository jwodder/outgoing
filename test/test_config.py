import platform
from   pydantic        import BaseModel
from   outgoing.config import DirectoryPath, FilePath, Path

if platform.system() == "Windows":
    home_var = "USERPROFILE"
else:
    home_var = "HOME"

class Paths(BaseModel):
    path: Optional[Path]
    filepath: Optional[FilePath]
    dirpath: Optional[DirectoryPath]

def test_path_expanduser(monkeypatch, tmp_path):
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.setenv(home_var, str(tmp_path))
    obj = Paths(path="~/nowhere", filepath="~/foo/bar.txt", dirpath="~/foo")
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"

def test_path_default_none():
    obj = Paths()
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None

def test_path_explicit_none():
    obj = Paths(path=None, filepath=None, dirpath=None)
    assert obj.path is None
    assert obj.filepath is None
    assert obj.dirpath is None
