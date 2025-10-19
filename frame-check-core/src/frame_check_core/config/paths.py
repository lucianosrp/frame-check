from collections.abc import Callable
import glob
from pathlib import Path


def normalize_path(path: Path | str) -> str:
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


def get_normalized_relative_path(
    root_path: Path, file_path: Path
) -> tuple[str, Path] | None:
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
        rel_path = file_path.resolve().relative_to(root_path.resolve())
        rel_path_normalized = normalize_path(rel_path)
        return rel_path_normalized, rel_path
    except ValueError:
        # File is outside root path
        return None


def matches_recursive_pattern(pattern: str, rel_path_str: str, rel_path: Path) -> bool:
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


def matches_directory_wildcard(pattern: str, rel_parts: tuple, rel_path: Path) -> bool:
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
        pattern_parts_normalized = [normalize_path(p) for p in pattern_parts]

        if len(rel_parts_to_check) == len(pattern_parts):
            match = True
            for pattern_part, path_part in zip(
                pattern_parts_normalized, rel_parts_to_check
            ):
                # Convert path_part to string with forward slashes
                path_part_str = normalize_path(path_part)
                if not fnmatch(path_part_str, pattern_part):
                    match = False
                    break
            return match
    else:
        # Handle simple dir/*.py pattern
        pattern_path = Path(pattern)
        pattern_dir = normalize_path(pattern_path.parent)
        pattern_filename = pattern_path.name

        # Match only files directly in the specified directory
        rel_parent_normalized = normalize_path(rel_path.parent)
        if rel_parent_normalized == pattern_dir:
            if fnmatch(rel_path.name, pattern_filename):
                return True

    return False


def matches_simple_filename_pattern(pattern: str, rel_path: Path) -> bool:
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


def matches_directory_prefix(pattern: str, rel_parts: tuple, rel_str: str) -> bool:
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
    pattern_normalized = normalize_path(pattern)
    pattern_parts = Path(pattern_normalized).parts

    # Check if the normalized path starts with the pattern
    if rel_str.startswith(pattern_normalized):
        return True

    # Alternative check using parts
    if len(rel_parts) >= len(pattern_parts):
        # Convert both sides to strings with forward slashes for comparison
        rel_parts_normalized = [
            normalize_path(p) for p in rel_parts[: len(pattern_parts)]
        ]
        pattern_parts_normalized = [normalize_path(p) for p in pattern_parts]

        if rel_parts_normalized == pattern_parts_normalized:
            return True

    return False


def matches_exact_path(pattern: str, rel_str: str, rel_path: Path) -> bool:
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
    pattern_normalized = normalize_path(pattern)

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

def matching_files(path: Path, recursive: bool, should_exclude: Callable[[Path], bool]) -> Path:
    collected_files: set[Path] = set()

    path = Path(path_str)

    if path.is_file() and path.suffix == ".py":
        collected_files.add(path.resolve())
    elif path.is_dir():
        # Recursively find all .py files in the directory
        collected_files.update(path.rglob("*.py"))
    else:
        # treat as a glob pattern
        for matched_path in glob.glob(path_str, recursive=True):
            matched = Path(matched_path)
            if matched.is_file() and matched.suffix == ".py":
                collected_files.add(matched.resolve())