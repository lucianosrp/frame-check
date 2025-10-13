from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from frame_check_core import FrameChecker
    from frame_check_core._models import Diagnostic


def print_diagnostics(fc: "FrameChecker", path: str) -> None:
    """Print formatted diagnostics to stdout."""
    if not fc.diagnostics:
        return

    lines = fc.source.splitlines() if fc.source else []

    for diag in fc.diagnostics:
        # Calculate max line number width for proper alignment
        max_line_num = diag.location[0]
        if diag.data_source_location:
            max_line_num = max(max_line_num, diag.data_source_location[0])
        line_width = len(str(max_line_num))

        _print_error_header(diag, path, line_width)
        _print_code_line(diag.location, lines, diag.underline_length, "^", line_width)
        _print_hints(diag.hint, line_width)

        if diag.data_source_location:
            _print_data_source_note(diag, lines, line_width)


def _print_error_header(diag: "Diagnostic", path: str, line_width: int) -> None:
    """Print the error header line with file path and message."""
    line_num, col_num = diag.location
    print(f"{path}:{line_num}:{col_num + 1} - {diag.severity}: {diag.message}")
    _print_gutter(line_width)


def _print_code_line(
    location: tuple[int, int],
    lines: list[str],
    underline_length: int,
    underline_char: str,
    line_width: int,
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
        print(f"{line_num:>{line_width}}|{stripped_line}")
        print(
            f"{' ' * line_width}|{' ' * relative_col}{underline_char * underline_length}"
        )
    else:
        print(f"{line_num:>{line_width}}| <line not available>")
        print(f"{' ' * line_width}|          {underline_char * 3}")

    _print_gutter(line_width)


def _print_hints(hints: list[str] | None, line_width: int, skip_first: int = 0) -> None:
    """Print hint messages.

    Args:
        hints: List of hint messages to print
        line_width: Width for line number formatting
        skip_first: Number of initial hints to skip
    """
    if not hints:
        return

    for hint_line in hints[skip_first:]:
        print(f"{' ' * line_width}| {hint_line}")

    _print_gutter(line_width)
    print()


def _print_data_source_note(
    diag: "Diagnostic", lines: list[str], line_width: int
) -> None:
    """Print the data source note section."""
    assert diag.data_source_location is not None

    print("--- Note: Data defined here with these columns ---")
    _print_gutter(line_width)
    _print_code_line(
        diag.data_source_location,
        lines,
        len(_get_line(lines, diag.data_source_location[0]) or ""),
        "~",
        line_width,
    )
    _print_hints(diag.hint, line_width, skip_first=1)


def _print_gutter(line_width: int) -> None:
    """Print a gutter separator line.

    Args:
        line_width: Width for line number formatting
    """
    print(f"{' ' * line_width}|")


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
