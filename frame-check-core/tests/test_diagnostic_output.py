from frame_check_core import FrameChecker
from frame_check_core._message import (
    print_diagnostics,
)


def test_print_diagnostics_format(capfd):
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
    checker = FrameChecker.check(code)
    assert len(checker.diagnostics) == 1
    diag = checker.diagnostics[0]
    assert diag.message == "Column 'NonExistentColumn' does not exist"
    assert diag.severity == "error"
    assert diag.location == (12, 2)
    assert diag.underline_length == 21
    assert isinstance(diag.hint, list)
    assert len(diag.hint) == 5
    assert (
        diag.hint[0]
        == "DataFrame 'df' created at line 10 from data defined at line 4 with columns:"
    )
    assert "  • Age" in diag.hint
    assert "  • City" in diag.hint
    assert "  • Name" in diag.hint
    assert "  • Salary" in diag.hint

    # Call print_diagnostics and capture output
    print_diagnostics(checker, "example.py")

    # Read captured output
    captured = capfd.readouterr()
    expected_output = f"""example.py:12:3 - error: Column 'NonExistentColumn' does not exist
  |
12|df["NonExistentColumn"]
  |  {"^" * 21}
  |
  | DataFrame 'df' created at line 10 from data defined at line 4 with columns:
  |   • Age
  |   • City
  |   • Name
  |   • Salary
  |

--- Note: Data defined here with these columns ---
  |
 4|data = {{
  |{"~" * 8}
  |
  |   • Age
  |   • City
  |   • Name
  |   • Salary
  |

"""
    assert captured.out.strip() == expected_output.strip()
