from pathlib import Path

import pytest
from frame_check_core import FrameChecker
from frame_check_core.models.region import CodePosition, CodeRegion

CSV_TEST_FILE = Path(__file__) / "data" / "csv_file.csv"


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
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b", "c"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=4, col=0),
        end=CodePosition(row=4, col=1),
    )
    assert frame_instance.data_src_region is not None
    assert frame_instance.data_src_region == CodeRegion(
        start=CodePosition(row=4, col=5),
        end=CodePosition(row=4, col=135),
    )


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
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b", "c"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=4, col=0),
        end=CodePosition(row=4, col=1),
    )
    assert frame_instance.data_src_region == CodeRegion(
        start=CodePosition(row=4, col=5),
        end=CodePosition(row=4, col=20),
    )


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
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b", "c"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=4, col=0),
        end=CodePosition(row=4, col=1),
    )
    assert frame_instance.data_src_region is not None
    assert frame_instance.data_src_region == CodeRegion(
        start=CodePosition(row=4, col=5),
        end=CodePosition(row=4, col=133),
    )
