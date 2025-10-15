import ast
from frame_check_core import FrameChecker
from unittest.mock import MagicMock, patch


def test_check_with_string_input():
    """Test FrameChecker.check() with string input."""
    code = """
import pandas as pd
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
value = df['C']
"""
    checker = FrameChecker.check(code)
    assert len(checker.column_accesses) == 1
    assert checker.column_accesses.contains_id("C")
    assert checker.column_accesses.get("C")[-1].id == "C"

    # Ensure the correct branch is taken
    with (
        patch("frame_check_core.frame_checker.ast.parse") as mock_ast_parse,
        patch("frame_check_core.frame_checker.open") as mock_open,
    ):
        checker = FrameChecker.check(code)
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

    checker = FrameChecker.check(ast_module)
    assert len(checker.frames.instances) == 1
    assert len(checker.column_accesses) == 1
    assert checker.column_accesses.contains_id("A")

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

    checker = FrameChecker.check(test_file)
    assert len(checker.column_accesses) == 1
    assert checker.column_accesses.contains_id("Z")

    mock_fd = MagicMock()
    mock_fd.__enter__().read.return_value = code
    # Ensure the correct branch is taken
    with (
        patch("frame_check_core.frame_checker.ast.parse") as mock_ast_parse,
        patch("frame_check_core.frame_checker.open", return_value=mock_fd) as mock_open,
    ):
        checker = FrameChecker.check(test_file)
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
    checker = FrameChecker.check(code)
    assert len(checker.column_accesses) == 1
    assert checker.column_accesses.contains_id("name")
    access = checker.column_accesses.get("name")[-1]
    assert access.id == "name"
    assert access.frame.id == "df"
    assert "name" in access.frame.columns


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
    checker = FrameChecker.check(code)
    assert len(checker.column_accesses) == 3
    assert checker.column_accesses.contains_id("A")
    assert checker.column_accesses.contains_id("C")
    assert checker.column_accesses.contains_id("X")


def test_check_pandas_alias():
    """Test that pandas imports with aliases are handled correctly."""
    code = """
import pandas as pd_alias
data = {'col1': [1, 2, 3], 'col2': [4, 5, 6]}
df = pd_alias.DataFrame(data)
result = df['col1']
"""
    checker = FrameChecker.check(code)
    assert len(checker.frames.instances) == 1
    assert len(checker.column_accesses) == 1
    assert checker.column_accesses.contains_id("col1")


def test_check_empty_code():
    """Test checking empty code."""
    checker = FrameChecker.check("")
    assert len(checker.frames.instances) == 0
    assert len(checker.column_accesses) == 0
    assert len(checker.import_aliases) == 0


def test_check_no_pandas_code():
    """Test checking code without pandas."""
    code = """
x = 5
y = x + 10
print(y)
"""
    checker = FrameChecker.check(code)
    assert len(checker.frames.instances) == 0
    assert len(checker.column_accesses) == 0
    assert len(checker.import_aliases) == 0
