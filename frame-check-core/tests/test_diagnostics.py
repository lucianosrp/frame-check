from frame_check_core import Diagnostic, FrameChecker


def test_diagnostics_data():
    code = """
import pandas as pd

data = {
    "Name": ["John", "Anna", "Peter", "Linda"],
    "Age": [28, 34, 29, 42],
    "City": ["New York", "Paris", "Berlin", "London"],
    "Salary": [65000, 70000, 62000, 85000],
}
# Create a sample DataFrame
df = pd.DataFrame(data)

# Non existent column
df["NonExistentColumn"]
    """

    fc = FrameChecker.check(code)
    assert fc.diagnostics == [
        Diagnostic(
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(14, 0),
            hint="DataFrame 'df' was defined at line 11 with columns:\n  • Age\n  • City\n  • Name\n  • Salary",
            definition_location=(4, 0),
        )
    ]


def test_diagnostics_in_df():
    code = """
import pandas as pd

df = pd.DataFrame(
{
    "Name": ["John", "Anna", "Peter", "Linda"],
    "Age": [28, 34, 29, 42],
    "City": ["New York", "Paris", "Berlin", "London"],
    "Salary": [65000, 70000, 62000, 85000],
}
)

# Non existent column
df["NonExistentColumn"]
    """

    fc = FrameChecker.check(code)
    assert fc.diagnostics == [
        Diagnostic(
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(14, 0),
            hint="DataFrame 'df' was defined at line 4 with columns:\n  • Age\n  • City\n  • Name\n  • Salary",
            definition_location=(5, 0),
        )
    ]
