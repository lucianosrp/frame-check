# mypy: ignore-errors
# ruff: noqa: F821
# TODO: Improve the message formatting in another PR
from typing import TYPE_CHECKING

from ..models.diagnostic import CodeSource, Severity

if TYPE_CHECKING:
    from ..frame_checker import FrameChecker
    from ..models.diagnostic import Diagnostic


# Terminal colors and formatting
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# String constants for formatting
GUTTER_CHAR = "│"
ERROR_VALUE = "error"
LINE_NOT_AVAILABLE = "<line not available>"
CARET = "^"
TILDE = "~"
SPACE = " "
DATA_SOURCE_NOTE = "--- Note: Data defined here with these columns ---"
LOCATION_FORMAT = "{path}:{line_num}:{col_num} - {severity}: {message}"
ERROR_LINE_FORMAT = "{line_num:>{width}} {gutter} {content}"
UNDERLINE_FORMAT = "{spaces:>{width}} {gutter} {indent}{color}{underline}{reset}"
HINT_LINE_FORMAT = "{spaces:>{width}} {gutter}  {hint_line}"


def print_diagnostics(fc: "FrameChecker", file=None, color: bool = True) -> None:
    """Print formatted diagnostics to stdout or a specified file."""
    if not fc.diagnostics:
        return

    lines = fc.source.code.splitlines() if fc.source.is_traceable else []

    for diag in fc.diagnostics:
        # Calculate max line number width for proper alignment

        max_line_num = diag.region.start.row
        if diag.data_src_region:
            max_line_num = max(max_line_num, diag.data_src_region.start.row)
        line_width = len(str(max_line_num))

        _print_error_header(diag, fc.source, line_width, file=file, color=color)
        _print_code_line(
            (diag.region.start.row, diag.region.start.col),
            lines,
            diag.region.col_span,
            CARET,
            line_width,
            file=file,
            color=color,
        )
        _print_hints(diag.hint, line_width, file=file)

        if diag.data_src_region:
            _print_data_source_note(diag, lines, line_width, file=file)


def _print_error_header(
    diag: "Diagnostic",
    source: CodeSource,
    line_width: int,
    file=None,
    color: bool = True,
) -> None:
    """Print the error header line with source and message."""
    line_num, col_num = diag.region.start.row, diag.region.start.col
    if color:
        diag_color = RED if diag.severity == Severity.ERROR else YELLOW
    else:
        diag_color = ""
    location_string = LOCATION_FORMAT.format(
        path=source.path.name if source.path is not None else "",
        line_num=line_num,
        col_num=col_num + 1,
        severity=diag.severity,
        message=diag.message,
    ).lstrip(":")  # Remove leading colon if path is empty
    print(
        f"{BOLD if color else ''}{diag_color}{location_string}{RESET if color else ''}",
        file=file,
    )
    underline = "───" + "┬" + "─" * (len(location_string) - 4)
    print(underline)
    _print_gutter(line_width, file=file)


def _print_code_line(
    location: tuple[int, int],
    lines: list[str],
    underline_length: int,
    underline_char: str,
    line_width: int,
    file=None,
    color: bool = True,
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
        print(
            ERROR_LINE_FORMAT.format(
                line_num=line_num,
                width=line_width,
                gutter=GUTTER_CHAR,
                content=stripped_line,
            ),
            file=file,
        )
        print(
            UNDERLINE_FORMAT.format(
                spaces=SPACE,
                width=line_width,
                gutter=GUTTER_CHAR,
                indent=SPACE * relative_col,
                color=YELLOW if color else "",
                underline=underline_char * underline_length,
                reset=RESET,
            ),
            file=file,
        )
    else:
        print(
            ERROR_LINE_FORMAT.format(
                line_num=line_num,
                width=line_width,
                gutter=GUTTER_CHAR,
                content=LINE_NOT_AVAILABLE,
            ),
            file=file,
        )
        print(
            UNDERLINE_FORMAT.format(
                spaces=SPACE,
                width=line_width,
                gutter=GUTTER_CHAR,
                indent=SPACE * 11,
                color=YELLOW if color else "",
                underline=underline_char * 3,
                reset=RESET,
            ),
            file=file,
        )

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
        print(
            HINT_LINE_FORMAT.format(
                spaces=SPACE, width=line_width, gutter=GUTTER_CHAR, hint_line=hint_line
            ),
            file=file,
        )

    _print_gutter(line_width, file=file)
    print(file=file)


def _print_data_source_note(
    diag: "Diagnostic", lines: list[str], line_width: int, file=None
) -> None:
    """Print the data source note section."""
    assert diag.data_source_location is not None

    print(DATA_SOURCE_NOTE, file=file)
    _print_gutter(line_width, file=file)
    _print_code_line(
        diag.data_source_location,
        lines,
        len(_get_line(lines, diag.data_source_location[0]) or ""),
        TILDE,
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
    print(f"{SPACE * line_width} {GUTTER_CHAR} ", file=file)


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
