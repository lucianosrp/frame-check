"""Tests for the Checker.check() method."""

from pathlib import Path

from frame_check_core.checker import Checker


def test_check_with_string_input():
    """Test Checker.check() with string input."""
    code = """
import pandas as pd
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
value = df['C']
"""
    checker = Checker.check(code)
    assert len(checker.dfs) == 1
    assert "df" in checker.dfs
    # Accessing non-existent column 'C' should produce a diagnostic
    assert len(checker.diagnostics) == 1


def test_check_with_file_input(tmp_path: Path):
    """Test Checker.check() with file input."""
    code = """
import pandas as pd
data = {'X': [1, 2], 'Y': [3, 4]}
df = pd.DataFrame(data)
result = df['Z']
"""
    test_file = tmp_path / "test_code.py"
    test_file.write_text(code)

    checker = Checker.check(test_file)
    assert len(checker.dfs) == 1
    assert "df" in checker.dfs
    # Accessing non-existent column 'Z' should produce a diagnostic
    assert len(checker.diagnostics) == 1


def test_check_valid_column_access():
    """Test that valid column access produces no diagnostics."""
    code = """
import pandas as pd
data = {'name': ['Alice', 'Bob'], 'age': [25, 30]}
df = pd.DataFrame(data)
names = df['name']
"""
    checker = Checker.check(code)
    assert len(checker.dfs) == 1
    tracker = checker.dfs.get("df")
    assert tracker is not None
    assert set(tracker.columns.keys()) == {"name", "age"}
    # Valid column access should produce no diagnostics
    assert len(checker.diagnostics) == 0


def test_check_multiple_dataframes():
    """Test checking code with multiple DataFrames."""
    code = """
import pandas as pd
data1 = {'A': [1, 2], 'B': [3, 4]}
df1 = pd.DataFrame(data1)
data2 = {'C': [5, 6], 'D': [7, 8]}
df2 = pd.DataFrame(data2)
val1 = df1['A']
val2 = df2['C']
val3 = df1['X']  # Invalid column
"""
    checker = Checker.check(code)
    assert len(checker.dfs) == 2
    assert "df1" in checker.dfs
    assert "df2" in checker.dfs
    assert set(checker.dfs["df1"].columns.keys()) == {"A", "B"}
    assert set(checker.dfs["df2"].columns.keys()) == {"C", "D"}
    # Only df1['X'] should produce a diagnostic
    assert len(checker.diagnostics) == 1


def test_check_pandas_alias():
    """Test that pandas imports with aliases are handled correctly."""
    code = """
import pandas as pd_alias
data = {'col1': [1, 2, 3], 'col2': [4, 5, 6]}
df = pd_alias.DataFrame(data)
result = df['col1']
"""
    checker = Checker.check(code)
    assert len(checker.dfs) == 1
    assert "df" in checker.dfs
    assert "pd_alias" in checker.pandas_aliases
    assert len(checker.diagnostics) == 0


def test_check_empty_code():
    """Test checking empty code."""
    checker = Checker.check("")
    assert len(checker.dfs) == 0
    assert len(checker.pandas_aliases) == 0
    assert len(checker.diagnostics) == 0


def test_check_no_pandas_code():
    """Test checking code without pandas."""
    code = """
x = 5
y = x + 10
print(y)
"""
    checker = Checker.check(code)
    assert len(checker.dfs) == 0
    assert len(checker.pandas_aliases) == 0
    assert len(checker.diagnostics) == 0
