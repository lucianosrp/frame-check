from collections.abc import Iterable, Iterator
import glob
from pathlib import Path


def normalize_pattern(pattern: str, recursive: bool) -> str:
    """Normalize a pattern string for consistent matching."""
    path_pattern = absolute_path(pattern)
    if pattern.endswith("/") or path_pattern.is_dir():
        suffix = "/**" if recursive else "/*"
        return path_pattern.as_posix() + suffix
    else:
        return path_pattern.as_posix()


def normalized_path_str(path: Path | str) -> str:
    """Normalize a path by resolving it to an absolute path and
    converting it to a string with forward slashes.

    Args:
        path: A path object or string to normalize.

    Returns:
        String representation of the path with forward slashes regardless of platform.

    This ensures consistent pattern matching across different operating systems.
    """
    return absolute_path(path).as_posix()


def absolute_path(path: Path | str) -> Path:
    """Get the absolute path from the current working directory."""
    return Path(path).resolve()


def any_match(absolute_path: Path, patterns: Iterable[str]) -> bool:
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
        - 'dir/**' (equivalent to 'dir/**', matches all files in dir and its subdirectories)

    This function handles both Unix-style and Windows-style paths, normalizing them to use
    forward slashes for consistent cross-platform pattern matching.
    """
    return any(absolute_path.full_match(pattern) for pattern in patterns)


def parse_filepath(file_str: str, recursive: bool) -> Iterator[Path]:
    """Parse a filepath or glob string into an iterator of absolute path objects."""
    path = absolute_path(file_str)
    if file_str.endswith("/") or path.is_dir() or not path.is_file():
        return (
            Path(file)
            for file in glob.glob(
                normalize_pattern(file_str, recursive),
                recursive=recursive,
                include_hidden=True,
            )
        )
    else:
        return iter((path,))


def collect_python_files(
    filepaths: Iterable[str], exclusion_patterns: Iterable[str], recursive: bool
) -> list[Path]:
    """Collect all Python files from the given paths.

    Args:
        paths: List of file paths, directory paths, or glob patterns.
        config: Config object with exclusion patterns.

    Returns:
        List of Path objects for Python files to check.
    """
    print(list(iter(exclusion_patterns)))
    return sorted(
        file
        for file_pattern in filepaths
        for file in parse_filepath(file_pattern.strip(), recursive)
        if file.suffix.lower() == ".py"
        and not any_match(file, iter(exclusion_patterns))
    )
