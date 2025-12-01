"""Tests for diagnostic generation."""

from frame_check_core.checker import Checker
from frame_check_core.diagnostic import Severity


def test_diagnostics_nonexistent_column():
    """Test diagnostic for accessing a non-existent column."""
    code = """
import pandas as pd

data = {
    "Name": ["John", "Anna", "Peter", "Linda"],
    "Age": [28, 34, 29, 42],
    "City": ["New York", "Paris", "Berlin", "London"],
    "Salary": [65000, 70000, 62000, 85000],
}
df = pd.DataFrame(data)

df["NonExistentColumn"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert diag.severity == Severity.ERROR
    assert "NonExistentColumn" in diag.message
    assert "does not exist" in diag.message
    assert diag.region is not None


def test_diagnostics_inline_dataframe():
    """Test diagnostic when DataFrame is created inline."""
    code = """
import pandas as pd

df = pd.DataFrame(
{
    "Name": ["John", "Anna", "Peter", "Linda"],
    "Age": [28, 34, 29, 42],
}
)

df["NonExistentColumn"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert diag.severity == Severity.ERROR
    assert "NonExistentColumn" in diag.message
    assert "does not exist" in diag.message


def test_diagnostics_multi_col_access():
    """Test multiple diagnostics for multiple invalid column accesses."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John", "Anna"]})

df["NonExistent1"]
df["NonExistent2"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 2

    assert "NonExistent1" in fc.diagnostics[0].message
    assert "NonExistent2" in fc.diagnostics[1].message


def test_diagnostics_col_access_before_assignment():
    """Test diagnostic when column is accessed before it's assigned."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John", "Anna"]})

df["NameLower"]
df["NameLower"] = df["Name"].str.lower()
    """

    fc = Checker.check(code)
    # Should have 1 diagnostic for accessing NameLower before it exists
    assert len(fc.diagnostics) == 1
    assert "NameLower" in fc.diagnostics[0].message
    assert "does not exist" in fc.diagnostics[0].message


def test_diagnostics_with_similarity_suggestion():
    """Test diagnostic includes suggestion for similar column name."""
    code = """
import pandas as pd

data = {
    "employee_name": ["Alice", "Bob"],
    "employee_id": [1001, 1002],
}
df = pd.DataFrame(data)

df["EmpolyeeName"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert "EmpolyeeName" in diag.message
    # Should suggest the similar column name
    assert "employee_name" in diag.message
    assert "Did you mean" in diag.message


def test_diagnostics_available_columns_listed():
    """Test that available columns are listed in diagnostic message."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
df["X"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert "Available columns" in diag.message
    assert "'A'" in diag.message
    assert "'B'" in diag.message
    assert "'C'" in diag.message


def test_no_diagnostics_for_valid_access():
    """Test no diagnostics when accessing valid columns."""
    code = """
import pandas as pd

df = pd.DataFrame({"Name": ["John"], "Age": [28]})
name = df["Name"]
age = df["Age"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 0


def test_diagnostics_assignment_with_missing_dependency():
    """Test diagnostic when assignment references non-existent column."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
df["C"] = df["X"] + df["Y"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert "Cannot assign" in diag.message
    # Should mention the missing columns
    assert "X" in diag.message or "Y" in diag.message


def test_diagnostics_undeclared_dataframe():
    """Test diagnostic when assignment references undeclared DataFrame."""
    code = """
import pandas as pd

df = pd.DataFrame({"A": [1, 2]})
unknown_df["column"] = df["A"]
    """

    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1

    diag = fc.diagnostics[0]
    assert "not declared" in diag.message
