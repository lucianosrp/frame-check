from frame_check_core import FrameChecker


def test_direct_column_assignment():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df["c"] = [7, 8, 9]
"""
    fc = FrameChecker.check(code)
    dfs = fc.frames.get("df")
    df = dfs[-1]
    assert df.columns == ["a", "b", "c"]
