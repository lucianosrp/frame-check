from frame_check_core.checker import Checker


def test_frame_init_dict_arg():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b"}


def test_frame_init_list_of_dict_arg():
    code = """
import pandas as pd

df = pd.DataFrame([{"a": 1, "b": 4 }, {"a": 2, "b": 5 }, {"a": 3, "b": 6 }])
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b"}


def test_frame_init_dict_var_arg():
    code = """
import pandas as pd

data = {"a": [1, 2, 3], "b": [4, 5, 6]}
df = pd.DataFrame(data)
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b"}
