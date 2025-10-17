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
        """Check if a file should be excluded based on patterns.

        The function supports various pattern types:
        - Simple paths: 'dir/file.py' (matches exact path)
        - Directory prefixes: 'dir/' (matches all files in dir and its subdirectories)
        - Simple filename patterns: '*.py' (matches all .py files in the root)
        - Directory wildcards: 'src/*.py' (matches .py files directly in src/)
        - Recursive wildcards: '**/*.py' (matches .py files in any subdirectory)
        - Directory with wildcards: 'src/*/file.py' (matches file.py in any direct subdirectory of src/)
        """
        if not self.exclude:
            return False

        # Get relative path from root
        try:
            rel_path = file_path.resolve().relative_to(self.root_path.resolve())
        except ValueError:
            # File is outside root path
            return False

        rel_parts = rel_path.parts
        rel_str = str(rel_path)

        for pattern in self.exclude:
            pattern = pattern.rstrip("/")

            # Handle wildcard patterns (*, ?, [])
            if any(c in pattern for c in ["*", "?", "["]):
                from fnmatch import fnmatch

                # Handle ** recursive glob pattern (matches any number of directories)
                if "**" in pattern:
                    parts = pattern.split("**/")
                    if len(parts) == 2:
                        prefix, suffix = parts
                        # Check if the path has the right prefix (if any)
                        if not prefix or rel_str.startswith(prefix):
                            # Check if the path ends with the right suffix
                            if fnmatch(rel_path.name, Path(suffix).name):
                                return True

                # Handle wildcards in directory/file pattern like "dir/*.py"
                elif "/" in pattern:
                    # Handle patterns with wildcards in the directory part
                    if "*" in Path(pattern).parent.as_posix():
                        # Split into parts and match each part
                        pattern_parts = Path(pattern).parts
                        rel_parts_to_check = rel_parts[: len(pattern_parts)]

                        if len(rel_parts_to_check) == len(pattern_parts):
                            match = True
                            for pattern_part, path_part in zip(
                                pattern_parts, rel_parts_to_check
                            ):
                                if not fnmatch(path_part, pattern_part):
                                    match = False
                                    break
                            if match:
                                return True
                    else:
                        # Handle simple dir/*.py pattern
                        pattern_path = Path(pattern)
                        pattern_dir = str(pattern_path.parent)
                        pattern_filename = pattern_path.name

                        # Match only files directly in the specified directory
                        if str(rel_path.parent) == pattern_dir:
                            if fnmatch(rel_path.name, pattern_filename):
                                return True
                else:
                    # For simple filename patterns like "*.py"
                    if fnmatch(rel_path.name, pattern):
                        return True

            # Simple directory prefix check
            elif "/" in pattern:
                # It's a simple path like ".venv" or "tests/fixtures"
                pattern_parts = Path(pattern).parts
                # Check if pattern is a prefix of the file path
                if len(rel_parts) >= len(pattern_parts):
                    if rel_parts[: len(pattern_parts)] == pattern_parts:
                        return True

            # Simple filename or exact path matches
            else:
                # Handle exact path match
                if pattern == rel_str:
                    return True

                # Handle directory matches (when a path starts with pattern/)
                if rel_str.startswith(pattern + "/"):
                    return True

                # Handle simple filename matches
                if pattern == rel_path.name:
                    return True

        return False
