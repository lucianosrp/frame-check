"""Tests for diagnostic output formatting."""

from pathlib import Path

from frame_check_core.checker import Checker, format_diagnostic


def test_format_diagnostic_with_string():
    """Test format_diagnostic produces expected output format."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John"], "Age": [28]})
df["NonExistent"]
"""
    checker = Checker.check(code)
    assert len(checker.diagnostics) == 1

    diag = checker.diagnostics[0]
    output = format_diagnostic(diag, "example.py")

    # Should have format: file:line:col: message
    assert output.startswith("example.py:")
    assert "NonExistent" in output
    assert "does not exist" in output


def test_format_diagnostic_with_path():
    """Test format_diagnostic works with Path object."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1, 2]})
df["X"]
"""
    checker = Checker.check(code)
    assert len(checker.diagnostics) == 1

    diag = checker.diagnostics[0]
    output = format_diagnostic(diag, Path("test_file.py"))

    assert output.startswith("test_file.py:")


def test_format_diagnostic_default_path():
    """Test format_diagnostic uses default path when not provided."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1]})
df["Missing"]
"""
    checker = Checker.check(code)
    assert len(checker.diagnostics) == 1

    diag = checker.diagnostics[0]
    output = format_diagnostic(diag)

    assert output.startswith("<unknown>:")
