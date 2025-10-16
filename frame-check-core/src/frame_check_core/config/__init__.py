import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def handle_pyproject(cls: "Config", config: dict[str, Any]) -> "Config":
    frame_check_table = config.get("tool", {}).get("frame-check", {})
    cls.exclude = set(frame_check_table.get("exclude", []))
    return cls


def handle_frame_check_toml(cls: "Config", config: dict[str, Any]) -> "Config":
    cls.exclude = set(config.get("exclude", []))
    return cls


@dataclass
class Config:
    root_path: Path = field(default=Path.cwd())
    exclude: set[str] | None = None

    @classmethod
    def load_from(cls, file: str | Path):
        with open(file, "rb") as f:
            config = tomllib.load(f)
            _class = cls(root_path=Path(file).parent)
            if Path(file).name == "pyproject.toml":
                _class = handle_pyproject(_class, config)
            elif Path(file).name == "frame-check.toml":
                _class = handle_frame_check_toml(_class, config)
            assert _class.exclude is not None, (
                "exclude should not be None at this point"
            )
            _class.exclude.add(".venv/")
        return _class

    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on patterns."""
        if not self.exclude:
            return False

        # Get relative path from root
        try:
            rel_path = file_path.resolve().relative_to(self.root_path.resolve())
        except ValueError:
            # File is outside root path
            return False

        rel_parts = rel_path.parts

        for pattern in self.exclude:
            pattern = pattern.rstrip("/")

            # Simple directory prefix check
            if "/" in pattern and not any(c in pattern for c in ["*", "?", "["]):
                # It's a simple path like ".venv" or "tests/fixtures"
                pattern_parts = Path(pattern).parts
                # Check if pattern is a prefix of the file path
                if len(rel_parts) >= len(pattern_parts):
                    if rel_parts[: len(pattern_parts)] == pattern_parts:
                        return True
            else:
                # For patterns with wildcards, use string matching
                # Convert to string comparison (can enhance with fnmatch if needed)
                rel_str = str(rel_path)
                if pattern in rel_str or rel_str.startswith(pattern + "/"):
                    return True

        return False
