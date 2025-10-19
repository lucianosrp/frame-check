from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..frame_checker import FrameChecker
    from ..models.diagnostic import Diagnostic


def print_diagnostics(fc: "FrameChecker", path: str, file=None) -> None:
    """Print formatted diagnostics to stdout or a specified file."""
    if not fc.diagnostics:
        return

    lines = fc.source.splitlines() if fc.source else []

    for diag in fc.diagnostics:
        # Calculate max line number width for proper alignment
        max_line_num = diag.loc[0]
        if diag.data_src_loc:
            max_line_num = max(max_line_num, diag.data_source_location[0])
        line_width = len(str(max_line_num))

        _print_error_header(diag, path, line_width, file=file)
        _print_code_line(
            diag.location, lines, diag.underline_length, "^", line_width, file=file
        )
        _print_hints(diag.hint, line_width, file=file)

        if diag.data_source_location:
            _print_data_source_note(diag, lines, line_width, file=file)


def _print_error_header(
    diag: "Diagnostic", path: str, line_width: int, file=None
) -> None:
    """Print the error header line with file path and message."""
    line_num, col_num = diag.location
    print(
        f"{path}:{line_num}:{col_num + 1} - {diag.severity}: {diag.message}", file=file
    )
    _print_gutter(line_width, file=file)


def _print_code_line(
    location: tuple[int, int],
    lines: list[str],
    underline_length: int,
    underline_char: str,
    line_width: int,
    file=None,
) -> None:
    """Print a code line with underline highlighting.

    Args:
        location: Tuple of (line_number, column_number)
        lines: Source code lines
        underline_length: Length of the underline
        underline_char: Character to use for underlining (e.g., '^' or '~')
        line_width: Width for line number formatting
    """
    line_num, col_num = location
    code_line = _get_line(lines, line_num)

    if code_line is not None:
        stripped_line, relative_col = _strip_indent(code_line, col_num)
        print(f"{line_num:>{line_width}}|{stripped_line}", file=file)
        print(
            f"{' ' * line_width}|{' ' * relative_col}{underline_char * underline_length}",
            file=file,
        )
    else:
        print(f"{line_num:>{line_width}}| <line not available>", file=file)
        print(f"{' ' * line_width}|          {underline_char * 3}", file=file)

    _print_gutter(line_width, file=file)


def _print_hints(
    hints: list[str] | None, line_width: int, skip_first: int = 0, file=None
) -> None:
    """Print hint messages.

    Args:
        hints: List of hint messages to print
        line_width: Width for line number formatting
        skip_first: Number of initial hints to skip
        file: Optional file-like object to write to
    """
    if not hints:
        return

    for hint_line in hints[skip_first:]:
        print(f"{' ' * line_width}| {hint_line}", file=file)

    _print_gutter(line_width, file=file)
    print(file=file)


def _print_data_source_note(
    diag: "Diagnostic", lines: list[str], line_width: int, file=None
) -> None:
    """Print the data source note section."""
    assert diag.data_source_location is not None

    print("--- Note: Data defined here with these columns ---", file=file)
    _print_gutter(line_width, file=file)
    _print_code_line(
        diag.data_source_location,
        lines,
        len(_get_line(lines, diag.data_source_location[0]) or ""),
        "~",
        line_width,
        file=file,
    )
    _print_hints(diag.hint, line_width, skip_first=1, file=file)


def _print_gutter(line_width: int, file=None) -> None:
    """Print a gutter separator line.

    Args:
        line_width: Width for line number formatting
        file: Optional file-like object to write to
    """
    print(f"{' ' * line_width}|", file=file)


def _get_line(lines: list[str], line_num: int) -> str | None:
    """Get a line from source by line number (1-indexed).

    Args:
        lines: List of source code lines
        line_num: Line number (1-indexed)

    Returns:
        The line content or None if line number is out of bounds
    """
    if 0 <= line_num - 1 < len(lines):
        return lines[line_num - 1]
    return None


def _strip_indent(line: str, col_num: int) -> tuple[str, int]:
    """Strip leading whitespace and adjust column number accordingly.

    Args:
        line: The source line with potential indentation
        col_num: The original column number

    Returns:
        A tuple of (stripped_line, adjusted_col_num)
    """
    indent = len(line) - len(line.lstrip())
    stripped_line = line.lstrip()
    relative_col = max(0, col_num - indent)
    return stripped_line, relative_col
