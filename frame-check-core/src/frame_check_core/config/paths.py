from collections.abc import Iterable, Iterator, Sequence
import glob
from pathlib import Path
from fnmatch import fnmatch
import re


def normalize_pattern(pattern: str, recursive: bool) -> str:
    """
    Normalize a pattern string for consistent matching:
    - Converts the pattern to an absolute path.
    - Appends '/**' for recursive matching if the pattern is a directory
    - Converts patterns like "**foo" to "**/*foo" for simpler matching.
    """
    path_pattern = absolute_path(pattern)
    if pattern.endswith("/") or path_pattern.is_dir():
        suffix = "/**" if recursive else "/*"
        return normalize_doublestar(path_pattern.as_posix(), recursive) + suffix
    else:
        return normalize_doublestar(path_pattern.as_posix(), recursive)


def normalize_doublestar(pattern: str, recursive: bool) -> str:
    """
    Ensure that double stars only appear as directory separators if matching recursively,
    i.e. "foo**bar" becomes "foo*/**/*bar". Note that this will NOT match "foobar",
    so this needs to be handled as a special case (e.g. by adding a separate pattern replacing
    "foo**bar" with "foo*bar").
    
    For non-recursive matching, replace '**' with '*'.
    """
    if recursive:
        right_side_replaced = re.sub(r"\*\*([^/]+)", r"**/*\1", pattern)
        fully_replaced = re.sub(r"([^/]+)\*\*", r"\1*/**", right_side_replaced)
    else:
        fully_replaced = pattern.replace("**", "*")
    return fully_replaced


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


def path_parts_match(
    path_parts: Sequence[str], pattern_parts: Sequence[str]
) -> bool:
    """Recursively check if path parts match pattern parts, supporting '**'."""
    if path_parts and pattern_parts:
        if pattern_parts[0] == "**":
            if len(pattern_parts) > 1:
                pattern_index = 1
                next_pattern_part = pattern_parts[pattern_index]
                path_index = 0
                while path_index < len(path_parts) and not (
                    found_match := fnmatch(
                        path_parts[path_index], next_pattern_part
                    )
                ):
                    path_index += 1
                if found_match:
                    return path_parts_match(
                        path_parts[path_index + 1 :],
                        pattern_parts[pattern_index + 1 :],
                    )
                else:
                    return False
            else:
                # Trailing ** matches everything
                return True
        else:
            # Use fnmatch to handle non-recursive wildcards
            if fnmatch(path_parts[0], pattern_parts[0]):
                return path_parts_match(path_parts[1:], pattern_parts[1:])
            else:
                return False

    elif path_parts or pattern_parts:
        # Either pattern or path is exhausted before completed match
        return False
    else:
        return True


def path_match(absolute_path: Path, pattern: str) -> bool:
    """Check if a given absolute path matches a specific pattern."""
    try:
        # Everything except recursive patterns can be handled
        # by Path.match()
        return (
            path_parts_match(absolute_path.parts, Path(pattern).parts)
            if "**" in pattern
            else absolute_path.match(pattern)
        )
    except Exception as e:
        print(
            f"Warning: Exception while trying to match path {absolute_path} with pattern {pattern}: {e}. Treating as no match."
        )
        return False


def any_match(absolute_path: Path, patterns: Iterable[str]) -> bool:
    """
    Check if a file should be excluded based on patterns.

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
    # In Python 3.13+, this can be done with method on Path class
    # return any(absolute_path.full_match(pattern) for pattern in patterns)
    return any(path_match(absolute_path, pattern) for pattern in patterns)


def parse_filepath(file_str: str, recursive: bool) -> Iterator[Path]:
    """
    Parse a filepath or glob string into an iterator of absolute path objects.
    Directories (indicated by ending in '/' or being an actual directory)
    and glob patterns will be expanded to yield all matching files.
    """
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
    return sorted(
        file
        for file_pattern in filepaths
        for file in parse_filepath(file_pattern.strip(), recursive)
        if file.suffix.lower() == ".py"
        and not any_match(file, iter(exclusion_patterns))
    )
