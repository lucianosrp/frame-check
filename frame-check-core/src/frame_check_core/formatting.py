"""
Rich diagnostic formatting for CLI output.

This module provides functions for formatting diagnostics with:
- Terminal colors (red for errors, yellow for warnings)
- Box-style formatting with gutters
- Source code context with line numbers
- Caret underlines highlighting error positions
"""

from pathlib import Path

from frame_check_core import diagnostic

# Terminal colors and formatting
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

# String constants for formatting
GUTTER_CHAR = "|"
CARET = "^"
SPACE = " "


def format_diagnostic_rich(
    diag: diagnostic.Diagnostic,
    file_path: Path | str = "<unknown>",
    source_code: str | None = None,
    color: bool = True,
) -> str:
    """
    Format a diagnostic with file location, code context, and underlines.

    Produces rich output with:
    - Colored header showing file location and error message
    - Source code line with the error
    - Caret underline highlighting the error position
    - Available columns as a note

    Args:
        diag: The diagnostic to format.
        file_path: Path to the source file (for display purposes).
        source_code: The source code string (for displaying code context).
        color: Whether to use terminal colors (default: True).

    Returns:
        A formatted string with rich diagnostic output.

    Example:
        >>> diag = ...  # Diagnostic at line 10, column 4
        >>> format_diagnostic_rich(diag, "my_script.py", source_code)
        my_script.py:10:5: Column 'X' does not exist on DataFrame 'df'. Did you mean 'Y'?
           |
        10 | df['X']
           |    ^^^^
           |
           = available: A, B, Y
    """
    loc = diag.region.start
    lines: list[str] = []

    # Parse the message to extract main message, suggestion, and available columns
    main_msg, suggestion, available = _parse_message(diag.message)

    # Build header line - combine main message with suggestion inline
    if suggestion:
        header_msg = f"{main_msg}. Did you mean '{suggestion}'?"
    else:
        header_msg = f"{main_msg}."

    header = f"{file_path}:{loc.row}:{loc.col + 1}: {header_msg}"

    # Apply colors if enabled
    if color:
        diag_color = RED if diag.severity == diagnostic.Severity.ERROR else YELLOW
        header = f"{BOLD}{diag_color}{header}{RESET}"

    lines.append(header)

    # Calculate line width for alignment
    line_width = len(str(loc.row))

    # Add empty gutter line
    lines.append(f"{SPACE * line_width} {GUTTER_CHAR}")

    # Add source code line if available
    if source_code:
        source_lines = source_code.splitlines()
        if 0 <= loc.row - 1 < len(source_lines):
            code_line = source_lines[loc.row - 1]
            # Strip indent and adjust column
            stripped_line, relative_col = _strip_indent(code_line, loc.col)

            # Add the code line
            lines.append(f"{loc.row:>{line_width}} {GUTTER_CHAR} {stripped_line}")

            # Add underline with carets
            underline_length = diag.region.col_span
            caret_line = SPACE * relative_col + CARET * underline_length
            if color:
                caret_line = f"{YELLOW}{caret_line}{RESET}"
            lines.append(f"{SPACE * line_width} {GUTTER_CHAR} {caret_line}")

    # Add empty gutter line
    lines.append(f"{SPACE * line_width} {GUTTER_CHAR}")

    # Add available columns as a note if present
    if available:
        note = f"= available: {available}"
        if color:
            note = f"{BLUE}{note}{RESET}"
        lines.append(f"{SPACE * line_width} {note}")

    return "\n".join(lines)


def _parse_message(message: str) -> tuple[str, str | None, str | None]:
    """
    Parse the diagnostic message to extract components.

    Args:
        message: The full diagnostic message which may contain newlines.

    Returns:
        A tuple of (main_message, suggestion, available_columns).
    """
    msg_lines = message.split("\n")
    main_msg = msg_lines[0].rstrip(".")
    suggestion = None
    available = None

    for line in msg_lines[1:]:
        line = line.strip()
        if line.startswith("Did you mean:"):
            # Extract suggestion: "Did you mean: 'Name'?" -> "Name"
            suggestion = line.replace("Did you mean:", "").strip().strip("'?")
        elif line.startswith("Available columns:"):
            # Extract columns and simplify format
            cols_part = line.replace("Available columns:", "").strip()
            # Remove quotes and simplify
            available = cols_part.replace("'", "")

    return main_msg, suggestion, available


def _strip_indent(line: str, col_num: int) -> tuple[str, int]:
    """
    Strip leading whitespace and adjust column number accordingly.

    Args:
        line: The source line with potential indentation.
        col_num: The original column number.

    Returns:
        A tuple of (stripped_line, adjusted_col_num).
    """
    indent = len(line) - len(line.lstrip())
    stripped_line = line.lstrip()
    relative_col = max(0, col_num - indent)
    return stripped_line, relative_col
