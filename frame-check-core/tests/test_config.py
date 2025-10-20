import tempfile
from pathlib import Path

from frame_check_core.config import Config

default_venv_exclusion = f"{Path.cwd().as_posix()}/.venv/**"


def test_frame_check_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(f"{tmpdir}/frame-check.toml")
        with open(path, "w") as f:
            f.write("exclude = ['ignore-dir/']")
            f.flush()

        config = Config.load_from(path)
        assert config._exclude == {
            default_venv_exclusion,
            f"{Path.cwd().as_posix()}/ignore-dir/**",
        }
        assert config.nonrecursive is False


def test_pyproject_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(f"{tmpdir}/pyproject.toml")
        with open(path, "w") as f:
            f.write("[tool.frame-check]\nexclude = ['ignore-dir/']")
            f.flush()

        config = Config.load_from(path)
        assert config._exclude == {
            default_venv_exclusion,
            f"{Path.cwd().as_posix()}/ignore-dir/**",
        }
        assert config.nonrecursive is False


def test_loading_toml_with_nonrecursive():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(f"{tmpdir}/frame-check.toml")
        with open(path, "w") as f:
            f.write("nonrecursive = true")
            f.flush()

        config = Config.load_from(path)
        assert config.nonrecursive is True
        assert config.recursive is False
        assert config._exclude == {default_venv_exclusion}


def test_update_exclude():
    config = Config()
    initial_excludes = set(config._exclude)
    new_patterns = {"dir1/", "dir2/file.py"}
    config.update_exclude(new_patterns)
    expected_excludes = initial_excludes.union(
        {
            f"{Path.cwd().as_posix()}/dir1/**",
            f"{Path.cwd().as_posix()}/dir2/file.py",
        }
    )
    assert config._exclude == expected_excludes


def test_update_nonrecursive():
    config = Config()
    assert config.nonrecursive is False
    config.update(nonrecursive=True)
    assert config.nonrecursive is True
    assert config.recursive is False
