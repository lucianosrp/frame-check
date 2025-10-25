from pathlib import Path

import pytest
from frame_check_core import FrameChecker
from frame_check_core.models.region import CodeRegion

CSV_TEST_FILE = (Path(__file__).parent / "data" / "csv_file.csv").as_posix()


@pytest.mark.support(
    name="read_csv + usecols inline",
    code="#DCMS-6",
    example="df = pd.read_csv('file.csv', usecols=['a', 'b', 'c'])",
)
def test_read_csv_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}", usecols=['a', 'b', 'c'])
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_ids() == {"df"}
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == frozenset({"a", "b", "c"})
    assert frame_instance.region == frame_instance.defined_region
    assert frame_instance.region == CodeRegion.from_tuples(
        start=(4, 0),
        end=(5, 2),  # end is always exclusive
    )
    assert frame_instance.region.row_span == 1
    assert frame_instance.region.col_span == 2


@pytest.mark.xfail(reason="FrameInstance to be refactored")
@pytest.mark.support(
    name="read_csv + usecols indirect",
    code="#DCMS-6-1",
    example="cols=['a', 'b', 'c']; df = pd.read_csv('file.csv', usecols=cols)",
)
def test_read_csv_usecols_indirect():
    code = f"""
import pandas as pd
cols = ['a', 'b', 'c']
df = pd.read_csv("{CSV_TEST_FILE}", usecols=cols)
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_ids() == {"df"}
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == frozenset({"a", "b", "c"})
    assert frame_instance.region == frame_instance.defined_region
    assert frame_instance.region == CodeRegion.from_tuples(
        start=(4, 0),
        end=(5, 2),  # end is always exclusive
    )
    assert frame_instance.region.row_span == 1
    assert frame_instance.region.col_span == 2


def test_read_csv_no_usecols():
    code = f"""
import pandas as pd

df = pd.read_csv("{CSV_TEST_FILE}")
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_ids() == set()


def test_read_csv_usecols_with_var():
    code = f"""
import pandas as pd
a = 'a'
df = pd.read_csv("{CSV_TEST_FILE}", usecols=[a, 'b', 'c'])
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_ids() == {"df"}
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == frozenset({"a", "b", "c"})
    assert frame_instance.region == frame_instance.defined_region
    assert frame_instance.region == CodeRegion.from_tuples(
        start=(4, 0),
        end=(5, 2),  # end is always exclusive
    )
    assert frame_instance.region.row_span == 1
    assert frame_instance.region.col_span == 2
