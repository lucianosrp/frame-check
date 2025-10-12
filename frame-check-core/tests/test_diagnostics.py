from frame_check_core import Diagnostic, FrameChecker


def test_diagnostics_data():
    # best similarity = 0.585 (<= 0.9)

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
    # best similarity = 0.585 (<= 0.9)

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
    # similarity = 0.585 (<= 0.9)
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
        # similarity = 0.889 (<= 0.9)
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

def test_diagnostics_with_col_recommendation_for_similarity_above90percents():
    code = """
import pandas as pd

# Create a dictionary with example values for each column
data = {
    "employee_name": ["Alice Johnson", "Bob Smith", "Charlie Davis", "Dana Lee", "Evan Wright"],
    "employee_id": [1001, 1002, 1003, 1004, 1005],
    "paygrade": ["A1", "B2", "C3", "B2", "A1"],
    "dept": ["Infra_PROJ", "SOC", "Infra_BAU", "QA_service", "CSP"]
}

# Create the DataFrame
df = pd.DataFrame(data)

df["EmpolyeeName"]
    """

    fc = FrameChecker.check(code)
    assert fc.diagnostics == [
        # similarity = 0.985 (> 0.9)
        Diagnostic(
            column_name="EmpolyeeName",
            message="Column 'EmpolyeeName' does not exist, did you mean 'employee_name'?",
            severity="error",
            location=(15, 2),
            underline_length=16,
            hint=[
                "DataFrame 'df' created at line 13 from data defined at line 5 with columns:",
                "  • dept",
                "  • employee_id",
                "  • employee_name",
                "  • paygrade"
            ],
            definition_location=(13, 0),
            data_source_location=(5, 0),
        )
    ]