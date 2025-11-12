import pytest
from frame_check_core import FrameChecker


@pytest.mark.support(code="#CAM-1")
def test_direct_column_assignment():
    code = """
import pandas as pd
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df["c"] = [7, 8, 9]
"""
    fc = FrameChecker.check(code)
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"a", "b", "c"})


@pytest.mark.support(code="#CAM-10")
def test_list_column_assignment():
    code = """
import pandas as pd
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df[["c", "d"]] = [[7, 8, 9], [10, 11, 12]]
"""
    fc = FrameChecker.check(code)
    df_snapshot = fc.frame_museum.get("df").latest_instance
    assert df_snapshot is not None
    assert df_snapshot.columns == frozenset({"a", "b", "c", "d"})
