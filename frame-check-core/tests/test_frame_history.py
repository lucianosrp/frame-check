import pytest
from frame_check_core import FrameChecker


def test_simple_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""

    fc = FrameChecker.check(code)

    assert fc.frame_museum.instance_ids == {"df"}


@pytest.mark.xfail(reason="Not implemented yet", strict=True)
def test_reassign_frame_history():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df = df[["a"]]
"""

    fc = FrameChecker.check(code)

    assert fc.frame_museum.instance_ids == {"df"}
