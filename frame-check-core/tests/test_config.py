import tempfile

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
