from frame_check_core.checker import Checker


def test_simple_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""

    fc = Checker.check(code)

    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert set(tracker.columns.keys()) == {"a", "b"}
