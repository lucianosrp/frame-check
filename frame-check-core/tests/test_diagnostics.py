import pytest
from frame_check_core.frame_checker import Diagnostic, FrameChecker
from frame_check_core.models.diagnostic import Severity
from frame_check_core.models.region import CodeRegion


@pytest.mark.xfail(reason="Diagnostic to be refactored", strict=True)
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
            message="Column 'NonExistentColumn' does not exist.",
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(14, 3),
                end=(15, 22),
            ),
            hint=[
                "DataFrame 'df' created at line 11:0 with columns:",
                "  • Age",
                "  • City",
                "  • Name",
                "  • Salary",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(11, 0),
                end=(12, 2),
            ),
            data_src_region=None,
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
            message="Column 'NonExistentColumn' does not exist.",
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(14, 3),
                end=(15, 22),
            ),
            hint=[
                "DataFrame 'df' created at line 4:0 with columns:",
                "  • Age",
                "  • City",
                "  • Name",
                "  • Salary",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(4, 0),
                end=(5, 2),
            ),
            data_src_region=None,
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
            message="Column 'NonExistentColumn' does not exist.",
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(11, 3),
                end=(12, 22),
            ),
            hint=[
                "DataFrame 'df' created at line 4:0 with columns:",
                "  • Name",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(4, 0),
                end=(5, 2),
            ),
            data_src_region=None,
        ),
        Diagnostic(
            column_name="NonExistentColumn",
            message="Column 'NonExistentColumn' does not exist.",
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(12, 3),
                end=(13, 22),
            ),
            hint=[
                "DataFrame 'df' created at line 4:0 with columns:",
                "  • Name",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(4, 0),
                end=(5, 2),
            ),
            data_src_region=None,
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
            message="Column 'NameLower' does not exist.",
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(10, 3),
                end=(11, 14),
            ),
            hint=[
                "DataFrame 'df' created at line 4:0 with columns:",
                "  • Name",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(4, 0),
                end=(5, 2),
            ),
            data_src_region=None,
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
            severity=Severity.ERROR,
            region=CodeRegion.from_tuples(
                start=(15, 3),
                end=(16, 17),
            ),
            hint=[
                "DataFrame 'df' created at line 13:0 with columns:",
                "  • dept",
                "  • employee_id",
                "  • employee_name",
                "  • paygrade",
            ],
            definition_region=CodeRegion.from_tuples(
                start=(13, 0),
                end=(14, 2),
            ),
            data_src_region=None,
        )
    ]
