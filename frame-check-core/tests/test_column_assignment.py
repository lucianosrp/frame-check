import pytest
from frame_check_core import Checker


@pytest.mark.support(code="#CAM-1")
def test_direct_column_assignment():
    code = """
import pandas as pd
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df["c"] = [7, 8, 9]
"""
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert sorted(df.columns.keys()) == ["a", "b", "c"]
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-10")
def test_list_column_assignment():
    code = """
import pandas as pd
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df[["c", "d"]] = [[7, 8, 9], [10, 11, 12]]
"""
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert sorted(df.columns.keys()) == ["a", "b", "c", "d"]
    assert len(fc.diagnostics) == 0
