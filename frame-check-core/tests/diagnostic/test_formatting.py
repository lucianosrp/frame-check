"""Tests for rich diagnostic formatting."""

from pathlib import Path

from frame_check_core.checker import Checker
from frame_check_core.formatting import format_diagnostic_rich


def test_format_diagnostic_rich_basic():
    """Test format_diagnostic_rich produces expected output format."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John"], "Age": [28]})
df["NonExistent"]
"""
    checker = Checker.check(code)
    assert len(checker.diagnostics) == 1

    diag = checker.diagnostics[0]
    output = format_diagnostic_rich(diag, "example.py", source_code=code, color=False)

    # Check header contains file, line, column, and message
    assert "example.py:5:1" in output
    assert "NonExistent" in output
    assert "does not exist" in output

    # Check gutter formatting
    assert "|" in output

    # Check code line is shown
    assert 'df["NonExistent"]' in output

    # Check carets are present
    assert "^" in output

    # Check available columns note
    assert "= available:" in output


def test_format_diagnostic_rich_with_color():
    """Test format_diagnostic_rich includes ANSI color codes when enabled."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1]})
df["X"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    # With color
    output_color = format_diagnostic_rich(diag, "test.py", source_code=code, color=True)
    assert "\033[1m" in output_color  # BOLD
    assert "\033[31m" in output_color  # RED
    assert "\033[0m" in output_color  # RESET

    # Without color
    output_no_color = format_diagnostic_rich(
        diag, "test.py", source_code=code, color=False
    )
    assert "\033[1m" not in output_no_color
    assert "\033[31m" not in output_no_color


def test_format_diagnostic_rich_without_source():
    """Test format_diagnostic_rich works without source code."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1]})
df["Missing"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=None, color=False)

    # Should still have header and gutter formatting
    assert "test.py:" in output
    assert "|" in output

    # Should not have the code line (since no source provided)
    assert 'df["Missing"]' not in output

    # Should still have available columns
    assert "= available:" in output


def test_format_diagnostic_rich_with_path_object():
    """Test format_diagnostic_rich works with Path object."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1]})
df["X"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(
        diag, Path("my_script.py"), source_code=code, color=False
    )

    assert "my_script.py:" in output


def test_format_diagnostic_rich_with_suggestion():
    """Test format_diagnostic_rich shows 'Did you mean' suggestion inline."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John"], "Age": [28]})
df["Nmae"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=code, color=False)

    # Should include the suggestion inline in the header
    assert "Did you mean" in output
    assert "Name" in output

    # The suggestion should be on the same line as the error message
    first_line = output.split("\n")[0]
    assert "Did you mean" in first_line


def test_format_diagnostic_rich_indented_code():
    """Test format_diagnostic_rich handles indented code properly."""
    code = """
import pandas as pd

def process():
    df = pd.DataFrame({"A": [1]})
    df["Missing"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=code, color=False)

    # The code line should be stripped of leading indentation
    lines = output.split("\n")
    code_lines = [line for line in lines if 'df["Missing"]' in line]
    assert len(code_lines) == 1
    # Should show the stripped line (without leading spaces from function body)
    assert 'df["Missing"]' in code_lines[0]


def test_format_diagnostic_rich_line_number_alignment():
    """Test that line numbers are properly aligned."""
    # Create code with error on line > 9 to test multi-digit alignment
    code = """
import pandas as pd

# Comment 1
# Comment 2
# Comment 3
# Comment 4
# Comment 5
# Comment 6
df = pd.DataFrame({"A": [1]})
df["X"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=code, color=False)

    # Line 11 should be properly formatted
    assert "11" in output
    assert "|" in output


def test_format_diagnostic_rich_available_columns_note():
    """Test that available columns are shown as a note."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John"], "Age": [28], "City": ["NYC"]})
df["Wrong"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=code, color=False)

    # Check the available columns note format
    assert "= available:" in output
    assert "Age" in output
    assert "City" in output
    assert "Name" in output


def test_format_diagnostic_rich_no_suggestion():
    """Test format_diagnostic_rich without a suggestion (no similar column)."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1]})
df["CompletelyDifferent"]
"""
    checker = Checker.check(code)
    diag = checker.diagnostics[0]

    output = format_diagnostic_rich(diag, "test.py", source_code=code, color=False)

    # Should not have "Did you mean" since no similar column
    assert "Did you mean" not in output

    # Should still show available columns
    assert "= available:" in output
