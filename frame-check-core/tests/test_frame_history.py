import pytest
from frame_check_core import FrameChecker, FrameHistoryKey


def test_simple_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""

    fc = FrameChecker.check(code)

    assert fc.frames.frame_keys() == ["df"]
    assert list(fc.frames.frames.keys()) == [FrameHistoryKey(4, "df")]


@pytest.mark.xfail(reason="Not implemented yet")
def test_reassign_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df = df[["a"]]
"""

    fc = FrameChecker.check(code)

    assert fc.frames.frame_keys() == ["df"]
    assert list(fc.frames.frames.keys()) == [
        FrameHistoryKey(4, "df"),
        FrameHistoryKey(5, "df"),
    ]
