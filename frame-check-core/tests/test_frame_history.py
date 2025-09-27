import pytest

from frame_check_core import FrameChecker, LineIdKey


def test_simple_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""

    fc = FrameChecker.check(code)

    assert fc.frames.instance_keys() == ["df"]
    assert list(fc.frames.instances.keys()) == [LineIdKey(4, "df")]


@pytest.mark.xfail(reason="Not implemented yet")
def test_reassign_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df = df[["a"]]
"""

    fc = FrameChecker.check(code)

    assert fc.frames.instance_keys() == ["df"]
    assert list(fc.frames.instances.keys()) == [
        LineIdKey(4, "df"),
        LineIdKey(5, "df"),
    ]
