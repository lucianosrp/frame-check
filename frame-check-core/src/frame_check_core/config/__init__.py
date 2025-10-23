import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


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
        """Check if a file should be excluded based on patterns.

        The function supports various pattern types:
        - Simple paths: 'dir/file.py' (matches exact path)
        - Directory prefixes: 'dir/' (matches all files in dir and its subdirectories)
        - Simple filename patterns: '*.py' (matches all .py files in the root)
        - Directory wildcards: 'src/*.py' (matches .py files directly in src/)
        - Recursive wildcards: '**/*.py' (matches .py files in any subdirectory)
        - Directory with wildcards: 'src/*/file.py' (matches file.py in any direct subdirectory of src/)

        This function handles both Unix-style and Windows-style paths, normalizing them to use
        forward slashes for consistent cross-platform pattern matching.
        """
        if not self.exclude:
            return False

        # Get normalized relative path
        path_info = paths.get_normalized_relative_path(self.root_path, file_path)
        if path_info is None:
            return False

        rel_str, rel_path = path_info
        rel_parts = rel_path.parts

        for pattern in self.exclude:
            pattern = pattern.rstrip("/")

            # Handle wildcard patterns (*, ?, [])
            if any(c in pattern for c in ["*", "?", "["]):
                # Handle ** recursive glob pattern
                if "**" in pattern:
                    if paths.matches_recursive_pattern(pattern, rel_str, rel_path):
                        return True

                # Handle wildcards in directory/file pattern
                elif "/" in pattern:
                    if paths.matches_directory_wildcard(pattern, rel_parts, rel_path):
                        return True
                else:
                    # For simple filename patterns like "*.py"
                    if paths.matches_simple_filename_pattern(pattern, rel_path):
                        return True

            # Simple directory prefix check
            elif "/" in pattern:
                if paths.matches_directory_prefix(pattern, rel_parts, rel_str):
                    return True

            # Simple filename or exact path matches
            else:
                if paths.matches_exact_path(pattern, rel_str, rel_path):
                    return True

        return False
