import ast
from unittest.mock import MagicMock, patch

from frame_check_core import FrameChecker
from frame_check_core.models.region import CodeRegion


def test_check_with_string_input():
    """Test FrameChecker.check() with string input."""
    code = """
import pandas as pd
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
value = df['C']
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 1
    diagnostic = fc.diagnostics[0]
    assert diagnostic.message == "Column 'C' does not exist."
    assert diagnostic.region == CodeRegion.from_tuples(
        start=(5, 8),
        end=(6, 15),
    )
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"A", "B"})

    # Ensure the correct branch is taken
    with (
        patch("frame_check_core.frame_checker.ast.parse") as mock_ast_parse,
        patch("frame_check_core.frame_checker.open") as mock_open,
    ):
        FrameChecker.check(code)
        # Ensure the AST has parsed the code string
        mock_ast_parse.assert_called_once_with(code)
        mock_open.assert_not_called()


def test_check_with_ast_input():
    """Test FrameChecker.check() with AST input."""
    code = """
import pandas as pd
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
value = df['A']
"""
    ast_module = ast.parse(code)
    assert isinstance(ast_module, ast.Module)

    fc = FrameChecker.check(ast_module)
    assert len(fc.diagnostics) == 0
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"A", "B"})

    # Ensure the correct branch is taken
    with (
        patch("frame_check_core.frame_checker.ast.parse") as mock_ast_parse,
        patch("frame_check_core.frame_checker.open") as mock_open,
    ):
        FrameChecker.check(ast_module)
        # Ensure the AST parse method and file open method are not called
        mock_ast_parse.assert_not_called()
        mock_open.assert_not_called()


def test_check_with_file_input(tmp_path):
    """Test FrameChecker.check() with file input."""
    code = """
import pandas as pd
data = {'X': [1, 2], 'Y': [3, 4]}
df = pd.DataFrame(data)
result = df['Z']
"""
    test_file = tmp_path / "test_code.py"
    test_file.write_text(code)

    fc = FrameChecker.check(test_file)
    assert len(fc.diagnostics) == 1
    diagnostic = fc.diagnostics[0]
    assert diagnostic.message == "Column 'Z' does not exist."
    assert diagnostic.region == CodeRegion.from_tuples(
        start=(5, 9),
        end=(6, 16),
    )
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"X", "Y"})

    mock_fd = MagicMock()
    mock_fd.__enter__().read.return_value = code
    # Ensure the correct branch is taken
    with (
        patch("frame_check_core.frame_checker.ast.parse") as mock_ast_parse,
        patch("frame_check_core.frame_checker.open", return_value=mock_fd) as mock_open,
    ):
        FrameChecker.check(test_file)
        # Ensure both the AST parse method and file open method are called
        mock_ast_parse.assert_called_once_with(code)
        mock_open.assert_called_once_with(str(test_file), "r")
        mock_fd.__enter__().read.assert_called_once()


def test_check_valid_column_access():
    """Test that valid column access is tracked correctly."""
    code = """
import pandas as pd
data = {'name': ['Alice', 'Bob'], 'age': [25, 30]}
df = pd.DataFrame(data)
names = df['name']
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"name", "age"})


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
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 1
    diagnostic = fc.diagnostics[0]
    assert diagnostic.message == "Column 'X' does not exist."
    assert diagnostic.region == CodeRegion.from_tuples(
        start=(9, 7),
        end=(10, 15),
    )
    df1_snapshot = fc.frame_museum.get("df1").latest_instance
    assert df1_snapshot is not None
    assert df1_snapshot.columns == frozenset({"A", "B"})


def test_check_pandas_alias():
    """Test that pandas imports with aliases are handled correctly."""
    code = """
import pandas as pd_alias
data = {'col1': [1, 2, 3], 'col2': [4, 5, 6]}
df = pd_alias.DataFrame(data)
result = df['col1']
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"col1", "col2"})


def test_check_empty_code():
    """Test checking empty code."""
    fc = FrameChecker.check("")
    assert len(fc.diagnostics) == 0
    assert len(fc.frame_museum.instance_ids) == 0


def test_check_no_pandas_code():
    """Test checking code without pandas."""
    code = """
x = 5
y = x + 10
print(y)
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0
    assert len(fc.frame_museum.instance_ids) == 0
