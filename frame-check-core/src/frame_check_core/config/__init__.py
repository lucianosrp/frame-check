import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    root_path: Path = field(default=Path.cwd())
    exclude: set[str] = field(default_factory=lambda: {".venv/"})

    @classmethod
    def load_from(cls, file: str | Path):
        with open(file, "rb") as f:
            config = tomllib.load(f)
            _class = cls(root_path=Path(file).parent)

            match Path(file).name:
                case "pyproject.toml":
                    framecheck_table = config.get("tool", {}).get("frame-check", {})
                case "frame-check.toml":
                    framecheck_table = config
                case _:
                    raise ValueError(
                        "File for loading config should be either pyproject.toml or frame-check.toml"
                    )

            _class.exclude.update(framecheck_table.get("exclude", []))

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
