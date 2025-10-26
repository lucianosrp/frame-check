import pytest
from frame_check_core import FrameChecker


@pytest.mark.support(code="#CAM-9")
def test_insert():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.insert(0, "A", [1, 2, 3])
df["A"]
"""
    fc = FrameChecker.check(code)
    df = fc.frames.get("df")[-1]
    assert df.columns == frozenset({"A"})
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-7")
@pytest.mark.xfail(reason="Not implemented", strict=True)
def test_assign_create():
    code = """
import pandas as pd
df = pd.DataFrame({})
df = df.assign(A=[1, 2, 3])
df["A"]
"""
    fc = FrameChecker.check(code)
    df = fc.frames.get("df")[-1]
    assert df.columns == frozenset({"A"})
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-7-1")
@pytest.mark.xfail(reason="Not implemented", strict=True)
def test_assign_subscript():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.assign(A=[1, 2, 3])["A"]
"""
    fc = FrameChecker.check(code)
    df = fc.frames.get("df")[-1]
    assert df.columns == frozenset({"A"})
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-7-2")
@pytest.mark.xfail(reason="Not implemented", strict=True)
def test_assign_chain():
    code = """
import pandas as pd
df = pd.DataFrame({})
df = df.assign(A=[1, 2, 3]).assign(B=[4, 5, 6])
df["A"]
df["B"]
"""
    fc = FrameChecker.check(code)
    df = fc.frames.get("df")[-1]
    assert df.columns == frozenset({"A", "B"})
    assert len(fc.diagnostics) == 0
