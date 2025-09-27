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
            column_name="NonExistentColumn",
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(14, 2),
            underline_length=21,
            hint=[
                "DataFrame 'df' created at line 11 from data defined at line 4 with columns:",
                "  • Age",
                "  • City",
                "  • Name",
                "  • Salary",
            ],
            definition_location=(11, 0),
            data_source_location=(4, 0),
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
            column_name="NonExistentColumn",
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(14, 2),
            underline_length=21,
            hint=[
                "DataFrame 'df' created at line 4 with columns:",
                "  • Age",
                "  • City",
                "  • Name",
                "  • Salary",
            ],
            definition_location=(4, 0),
            data_source_location=None,
        )
    ]


def test_diagnostics_multi_col_access():
    code = """
import pandas as pd

df = pd.DataFrame(
{
    "Name": ["John", "Anna", "Peter", "Linda"],
}
)

# Non existent column
df["NonExistentColumn"]
df["NonExistentColumn"]
    """

    fc = FrameChecker.check(code)
    assert fc.diagnostics == [
        Diagnostic(
            column_name="NonExistentColumn",
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(11, 2),
            underline_length=21,
            hint=[
                "DataFrame 'df' created at line 4 with columns:",
                "  • Name",
            ],
            definition_location=(4, 0),
            data_source_location=None,
        ),
        Diagnostic(
            column_name="NonExistentColumn",
            message="Column 'NonExistentColumn' does not exist",
            severity="error",
            location=(12, 2),
            underline_length=21,
            hint=[
                "DataFrame 'df' created at line 4 with columns:",
                "  • Name",
            ],
            definition_location=(4, 0),
            data_source_location=None,
        ),
    ]


def test_diagnostics_col_access_before_assignment():
    code = """
import pandas as pd

df = pd.DataFrame(
{
    "Name": ["John", "Anna", "Peter", "Linda"],
}
)

df["NameLower"]
df["NameLower"] = df["Name"].str.lower()
    """

    fc = FrameChecker.check(code)
    assert fc.diagnostics == [
        Diagnostic(
            column_name="NameLower",
            message="Column 'NameLower' does not exist",
            severity="error",
            location=(10, 2),
            underline_length=13,
            hint=[
                "DataFrame 'df' created at line 4 with columns:",
                "  • Name",
            ],
            definition_location=(4, 0),
            data_source_location=None,
        ),
        # TODO: we could had a hint that says something like:
        # NameLower is later defined at line 11
    ]
