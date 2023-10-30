import pathlib
from typing import Optional
from pydantic import BaseModel, ValidationError
import pytest
from outgoing.config import DirectoryPath, FilePath, Path


class Paths(BaseModel):
    path: Optional[Path] = None
    filepath: Optional[FilePath] = None
    dirpath: Optional[DirectoryPath] = None


def test_path_expanduser(
    tmp_home: pathlib.Path,
) -> None:
    (tmp_home / "foo").mkdir()
    (tmp_home / "foo" / "bar.txt").touch()
    obj = Paths(path="~/nowhere", filepath="~/foo/bar.txt", dirpath="~/foo")
    assert obj.path == tmp_home / "nowhere"
    assert obj.filepath == tmp_home / "foo" / "bar.txt"
    assert obj.dirpath == tmp_home / "foo"


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


class ResolvingPaths(BaseModel):
    configpath: Optional[Path] = None
    path: Path
    filepath: FilePath
    dirpath: DirectoryPath


def test_path_resolve_to_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "bar" / "foo").mkdir(parents=True)
    (tmp_path / "bar" / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath="bar/quux.txt",
        path="nowhere",
        filepath="foo/bar.txt",
        dirpath="foo",
    )
    assert obj.configpath == tmp_path / "bar" / "quux.txt"
    assert obj.path == tmp_path / "bar" / "nowhere"
    assert obj.filepath == tmp_path / "bar" / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "bar" / "foo"


def test_path_resolve_to_curdir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath=None,
        path="nowhere",
        filepath="foo/bar.txt",
        dirpath="foo",
    )
    assert obj.configpath is None
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"


def test_path_resolve_absolute_configpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "foo").mkdir(parents=True)
    (tmp_path / "foo" / "bar.txt").touch()
    monkeypatch.chdir(tmp_path)
    obj = ResolvingPaths(
        configpath="bar/quux.txt",
        path=tmp_path / "nowhere",
        filepath=tmp_path / "foo" / "bar.txt",
        dirpath=tmp_path / "foo",
    )
    assert obj.configpath == tmp_path / "bar" / "quux.txt"
    assert obj.path == tmp_path / "nowhere"
    assert obj.filepath == tmp_path / "foo" / "bar.txt"
    assert obj.dirpath == tmp_path / "foo"
