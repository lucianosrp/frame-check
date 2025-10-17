import tomllib
from dataclasses import dataclass, field
from functools import cache
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

    def _normalize_path(self, path: Path | str) -> str:
        """Normalize a path to use forward slashes for cross-platform pattern matching.

        Args:
            path: A path object or string to normalize.

        Returns:
            String representation of the path with forward slashes regardless of platform.

        This ensures consistent pattern matching across different operating systems.
        """
        if isinstance(path, Path):
            return path.as_posix()
        return str(path).replace("\\", "/")

    def _get_normalized_relative_path(self, file_path: Path) -> tuple[str, Path] | None:
        """Get the normalized relative path from the root path.

        Args:
            file_path: The absolute path to normalize relative to the root path.

        Returns:
            A tuple containing (normalized_path_string, path_object) or None if the path
            is outside the root directory.

        This is used as the first step in path matching to handle paths relative to
        the project root consistently across platforms.
        """
        try:
            rel_path = file_path.resolve().relative_to(self.root_path.resolve())
            rel_path_normalized = self._normalize_path(rel_path)
            return rel_path_normalized, rel_path
        except ValueError:
            # File is outside root path
            return None

    def _matches_recursive_pattern(
        self, pattern: str, rel_path_str: str, rel_path: Path
    ) -> bool:
        """Check if a path matches a pattern with recursive wildcards (**/).

        Args:
            pattern: The exclude pattern containing **/ syntax (e.g., "**/vscode/**").
            rel_path_str: Normalized string representation of the relative path.
            rel_path: Path object representing the relative path.

        Returns:
            True if the path matches the recursive pattern, False otherwise.

        This handles patterns like "**/*.py" which match any .py file at any depth,
        or "**/vscode/**" which matches any file within any vscode directory at any depth.
        """
        from fnmatch import fnmatch

        parts = pattern.split("**/")
        if len(parts) == 2:
            prefix, suffix = parts
            # Check if the path has the right prefix (if any)
            if not prefix or rel_path_str.startswith(prefix):
                # Check if the path ends with the right suffix
                if fnmatch(rel_path.name, Path(suffix).name):
                    return True

                # Check if the path matches the **/ pattern with any directory
                if fnmatch(rel_path_str, f"**/{suffix}"):
                    return True
        return False

    def _matches_directory_wildcard(
        self, pattern: str, rel_parts: tuple, rel_path: Path
    ) -> bool:
        """Check if a path matches a pattern with wildcards in directory parts.

        Args:
            pattern: The exclude pattern containing wildcards in directory parts.
            rel_parts: Tuple of path parts from the relative path.
            rel_path: Path object representing the relative path.

        Returns:
            True if the path matches the directory wildcard pattern, False otherwise.

        This handles two types of patterns:
        1. Patterns with wildcards in directory names (e.g., "src/*/file.py")
        2. Simple directory/file patterns (e.g., "src/*.py") where only the filename
           contains wildcards
        """
        from fnmatch import fnmatch

        # Handle patterns with wildcards in the directory part
        if "*" in Path(pattern).parent.as_posix():
            # Split into parts and match each part
            pattern_parts = Path(pattern).parts
            rel_parts_to_check = rel_parts[: len(pattern_parts)]

            # Convert pattern parts to use forward slashes
            pattern_parts_normalized = [self._normalize_path(p) for p in pattern_parts]

            if len(rel_parts_to_check) == len(pattern_parts):
                match = True
                for pattern_part, path_part in zip(
                    pattern_parts_normalized, rel_parts_to_check
                ):
                    # Convert path_part to string with forward slashes
                    path_part_str = self._normalize_path(path_part)
                    if not fnmatch(path_part_str, pattern_part):
                        match = False
                        break
                return match
        else:
            # Handle simple dir/*.py pattern
            pattern_path = Path(pattern)
            pattern_dir = self._normalize_path(pattern_path.parent)
            pattern_filename = pattern_path.name

            # Match only files directly in the specified directory
            rel_parent_normalized = self._normalize_path(rel_path.parent)
            if rel_parent_normalized == pattern_dir:
                if fnmatch(rel_path.name, pattern_filename):
                    return True

        return False

    def _matches_simple_filename_pattern(self, pattern: str, rel_path: Path) -> bool:
        """Check if a filename matches a simple pattern like *.py.

        Args:
            pattern: The simple filename pattern (e.g., "*.py", "config.?").
            rel_path: Path object representing the relative path.

        Returns:
            True if the filename matches the pattern, False otherwise.

        This handles simple filename patterns that apply to the filename only,
        ignoring directory structure.
        """
        from fnmatch import fnmatch

        return fnmatch(rel_path.name, pattern)

    def _matches_directory_prefix(
        self, pattern: str, rel_parts: tuple, rel_str: str
    ) -> bool:
        """Check if a path matches a directory prefix pattern.

        Args:
            pattern: The directory prefix pattern (e.g., "tests/", ".venv/").
            rel_parts: Tuple of path parts from the relative path.
            rel_str: Normalized string representation of the relative path.

        Returns:
            True if the path starts with the directory prefix, False otherwise.

        This handles patterns that specify a directory prefix. Any file located within
        the specified directory or its subdirectories will match.
        Example: "vscode/" will match "vscode/file.py" and "vscode/subdir/file.py"
        """
        pattern_normalized = self._normalize_path(pattern)
        pattern_parts = Path(pattern_normalized).parts

        # Check if the normalized path starts with the pattern
        if rel_str.startswith(pattern_normalized):
            return True

        # Alternative check using parts
        if len(rel_parts) >= len(pattern_parts):
            # Convert both sides to strings with forward slashes for comparison
            rel_parts_normalized = [
                self._normalize_path(p) for p in rel_parts[: len(pattern_parts)]
            ]
            pattern_parts_normalized = [self._normalize_path(p) for p in pattern_parts]

            if rel_parts_normalized == pattern_parts_normalized:
                return True

        return False

    def _matches_exact_path(self, pattern: str, rel_str: str, rel_path: Path) -> bool:
        """Check if a path matches an exact path pattern.

        Args:
            pattern: The exact pattern to match (e.g., "file.py", "dir").
            rel_str: Normalized string representation of the relative path.
            rel_path: Path object representing the relative path.

        Returns:
            True if the path matches the exact pattern, False otherwise.

        This handles three types of exact matches:
        1. Exact path match: "dir/file.py" matches only "dir/file.py"
        2. Directory matches: "dir" matches "dir/file.py" (with a trailing slash check)
        3. Simple filename matches: "file.py" matches any file named "file.py" regardless of directory
        """
        pattern_normalized = self._normalize_path(pattern)

        # Handle exact path match
        if pattern_normalized == rel_str:
            return True

        # Handle directory matches (when a path starts with pattern/)
        if rel_str.startswith(pattern_normalized + "/"):
            return True

        # Handle simple filename matches
        if pattern == rel_path.name:
            return True

        return False

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
        path_info = self._get_normalized_relative_path(file_path)
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
                    if self._matches_recursive_pattern(pattern, rel_str, rel_path):
                        return True

                # Handle wildcards in directory/file pattern
                elif "/" in pattern:
                    if self._matches_directory_wildcard(pattern, rel_parts, rel_path):
                        return True
                else:
                    # For simple filename patterns like "*.py"
                    if self._matches_simple_filename_pattern(pattern, rel_path):
                        return True

            # Simple directory prefix check
            elif "/" in pattern:
                if self._matches_directory_prefix(pattern, rel_parts, rel_str):
                    return True

            # Simple filename or exact path matches
            else:
                if self._matches_exact_path(pattern, rel_str, rel_path):
                    return True

        return False
