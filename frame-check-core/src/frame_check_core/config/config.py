import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


@dataclass
class Config:
    root_path: Path = field(default=Path.cwd())
    exclude: set[str] = field(default_factory=lambda: {".venv/"})
    nonrecursive: bool = field(default=False)

    @classmethod
    def load_from(cls, file: Path):
        _class = cls(root_path=Path(file).parent)
        with open(file, "rb") as f:
            config = tomllib.load(f)
            if file.name == "pyproject.toml":
                config = config.get("tool", {}).get("frame-check", {})

            _class.exclude.update(config.get("exclude", []))

        return _class

    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on patterns.

        The function supports various pattern types:
        - Simple paths: 'dir/file.py' (matches exact path)
        - Single wildcards:
            - '*' (matches any characters in a filename or directory name, except path separators)
            - '?' (matches a single character, except path separators)
            - '[]' (matches any character in the specified set)
        - Recursive wildcard:
            - 'dir/**' (matches all files in dir and its subdirectories)
            - 'dir/**/file.py' (matches file.py dir and in any subdirectory of dir)
        - Recursive directories:
            - 'dir/' (equivalent to 'dir/**', matches all files in dir and its subdirectories)

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
