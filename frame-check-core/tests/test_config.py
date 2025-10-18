import os
import tempfile
from pathlib import Path

import pytest
from frame_check_core.config import Config


def test_frame_check_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/frame-check.toml"
        with open(path, "w") as f:
            f.write("exclude = ['ignore-dir/']")
            f.flush()

        config = Config.load_from(path)
        assert config.exclude == {".venv/", "ignore-dir/"}


def test_pyproject_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = f"{tmpdir}/pyproject.toml"
        with open(path, "w") as f:
            f.write("[tool.frame-check]\nexclude = ['ignore-dir/']")
            f.flush()

        config = Config.load_from(path)
        assert config.exclude == {".venv/", "ignore-dir/"}


@pytest.mark.parametrize(
    "exclude, target, should_exclude",
    [
        ({".tmp/"}, ".tmp/test/file.py", True),
        ({"file.py"}, "other_file.py", False),
        ({"file.py"}, "file.py", True),
        ({"dir/file.py"}, "dir/file.py", True),
        ({"dir/file.py"}, "dir/other_file.py", False),
        ({"dir/file.py"}, "other_dir/file.py", False),
        ({"dir/"}, "dir/file.py", True),
        ({"dir/"}, "dir/subdir/file.py", True),
        ({"dir/"}, "other_dir/file.py", False),
        ({"*.py"}, "file.py", True),
        ({"src/*.py"}, "src/file.py", True),
        ({"src/*.py"}, "src/subdir/file.py", False),
        ({"**/*.py"}, "src/subdir/file.py", True),
        ({"src/*/file.py"}, "src/subdir/file.py", True),
        ({"src/*/file.py"}, "src/another/other.py", False),
        ({"*.txt"}, "file.py", False),
        # Multiple exclude patterns
        ({"*.txt", "*.py"}, "file.py", True),
        ({"*.txt", "*.py"}, "file.txt", True),
        ({"*.txt", "*.py"}, "file.md", False),
        ({"src/", "tests/"}, "src/file.py", True),
        ({"src/", "tests/"}, "tests/file.py", True),
        ({"src/", "tests/"}, "docs/file.py", False),
        ({"src/*.py", "tests/*.py"}, "src/file.py", True),
        ({"src/*.py", "tests/*.py"}, "tests/file.py", True),
        ({"src/*.py", "tests/*.py"}, "src/subdir/file.py", False),
        # More complex combinations
        ({"**/*.py", "!src/"}, "src/file.py", True),
        ({"**/*.py", "!src/"}, "docs/file.py", True),
        ({"*.py", "src/**/*.txt"}, "src/subdir/file.txt", True),
        ({"*.py", "src/**/*.txt"}, "src/file.py", True),
        ({"*.py", "src/**/*.txt"}, "src/subdir/file.md", False),
        ({"dir/", "**/*.py", "*.md"}, "other/file.py", True),
    ],
)
def test_should_exclude(exclude: set[str], target: str, should_exclude: bool):
    # Setup
    temp_dir = tempfile.gettempdir()
    original_dir = os.getcwd()
    conf = Config(root_path=Path(temp_dir))
    conf.exclude = exclude
    target_path = Path(temp_dir) / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.touch()

    try:
        # Change directory and test
        os.chdir(temp_dir)
        assert conf.should_exclude(target_path) == should_exclude
    finally:
        # Cleanup
        if target_path.exists():
            target_path.unlink()
        # Return to original directory
        os.chdir(original_dir)
