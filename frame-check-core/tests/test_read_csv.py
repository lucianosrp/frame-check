from pathlib import Path

import pytest
from frame_check_core.checker import Checker

CSV_TEST_FILE = (Path(__file__).parent / "data" / "csv_file.csv").as_posix()


@pytest.mark.support(code="#DCMS-6")
def test_read_csv_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}", usecols=['a', 'b', 'c'])
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b", "c"}


@pytest.mark.support(code="#DCMS-6-1")
def test_read_csv_usecols_indirect():
    code = f"""
import pandas as pd
cols = ['a', 'b', 'c']
df = pd.read_csv("{CSV_TEST_FILE}", usecols=cols)
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b", "c"}


def test_read_csv_no_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}")
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == set()


def test_read_csv_usecols_with_var():
    code = f"""
import pandas as pd
a = 'a'
df = pd.read_csv("{CSV_TEST_FILE}", usecols=[a, 'b', 'c'])
"""
    fc = Checker.check(code)
    assert set(fc.dfs.keys()) == {"df"}
    tracker = fc.dfs.get("df")
    assert tracker is not None
    assert tracker.id_ == "df"
    assert set(tracker.columns.keys()) == {"a", "b", "c"}
