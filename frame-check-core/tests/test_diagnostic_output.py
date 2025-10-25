from pathlib import Path
import pytest
from frame_check_core import FrameChecker
from frame_check_core.util.message import (
    print_diagnostics,
)
from frame_check_core.models.region import CodePosition, CodeRegion


@pytest.mark.parametrize("has_file", [True, False])
def test_print_diagnostics_format(has_file: bool, tmp_path: Path, capfd):
    code = """
import pandas as pd

data = {
    "Name": ["John", "Anna"],
    "Age": [28, 34],
    "City": ["NYC", "LA"],
    "Salary": [50000, 60000],
}
df = pd.DataFrame(data)

df["NonExistentColumn"]
"""
    if has_file:
        code_file = tmp_path / "example.py"
        code_file.write_text(code)
        checker = FrameChecker.check(code_file)
    else:
        checker = FrameChecker.check(code)

    assert len(checker.diagnostics) == 1
    diag = checker.diagnostics[0]
    assert diag.message == "Column 'NonExistentColumn' does not exist."
    assert diag.severity == "error"
    assert diag.region == CodeRegion(
        start=CodePosition(row=12, col=3),
        end=CodePosition(row=13, col=22),
    )
    assert diag.region.row_span == 1
    assert diag.region.col_span == 19
    assert isinstance(diag.hint, list)
    assert len(diag.hint) == 5
    assert diag.hint[0] == "DataFrame 'df' created at line 10:0 with columns:"
    assert "  • Age" in diag.hint
    assert "  • City" in diag.hint
    assert "  • Name" in diag.hint
    assert "  • Salary" in diag.hint

    # Call print_diagnostics and capture output
    print_diagnostics(checker, color=False)

    # Read captured output
    captured = capfd.readouterr()
    output = captured.out

    # Test content instead of exact formatting

    error_line_prefix = ""
    if has_file:
        error_line_prefix = f"{code_file.name}:"

    assert (
        f"{error_line_prefix}12:3 - error: Column 'NonExistentColumn' does not exist."
        in output
    )
    assert 'df["NonExistentColumn"]' in output
    assert "DataFrame 'df' created at line 10:0 with columns with columns:" in output

    # Check that all columns are listed in the output
    assert "• Age" in output
    assert "• City" in output
    assert "• Name" in output
    assert "• Salary" in output
