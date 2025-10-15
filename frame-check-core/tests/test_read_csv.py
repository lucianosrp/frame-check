from frame_check_core import FrameChecker
from pathlib import Path

CSV_TEST_FILE = Path(__file__) / "data" / "csv_file.csv"


def test_read_csv_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}", usecols=['a', 'b', 'c'])
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b", "c"]
    assert frame_instance.lineno == 4


def test_read_csv_usecols_indirect():
    code = f"""
import pandas as pd
cols = ['a', 'b', 'c']
df = pd.read_csv("{CSV_TEST_FILE}", usecols=cols)
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b", "c"]
    assert frame_instance.lineno == 4
    assert frame_instance.data_source_lineno == 3


def test_read_csv_no_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}")
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == []


def test_read_csv_usecols_with_var():
    code = f"""
import pandas as pd
a = 'a'
df = pd.read_csv("{CSV_TEST_FILE}", usecols=[a, 'b', 'c'])
"""
    fc = FrameChecker.check(code)
    # ! Non-string lists are ignored
    assert fc.frames.instance_keys() == []
    # assert fc.frames.instance_keys() == ["df"]
    # frame_instance = fc.frames.get_at(4, "df")
    # assert frame_instance is not None
    # assert frame_instance.id == "df"
    # assert frame_instance.columns == ["a", "b", "c"]
    # assert frame_instance.lineno == 4
