import pytest

from frame_check_core import FrameChecker


def test_insert():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.insert(0, "A", [1, 2, 3])
df["A"]
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0


@pytest.mark.xfail(reason="Not implemented")
def test_assign_create():
    code = """
import pandas as pd
df = pd.DataFrame({})
df = df.assign(A=[1, 2, 3])
df["A"]
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0


@pytest.mark.xfail(reason="Not implemented")
def test_assign_subscript():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.assign(A=[1, 2, 3])["A"]
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0


@pytest.mark.xfail(reason="Not implemented")
def test_assign_chain():
    code = """
import pandas as pd
df = pd.DataFrame({})
df = df.assign(A=[1, 2, 3]).assign(B=[4, 5, 6])
df["A"]
df["B"]
"""
    fc = FrameChecker.check(code)
    assert len(fc.diagnostics) == 0
