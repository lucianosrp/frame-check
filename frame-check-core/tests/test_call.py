import pytest
from frame_check_core.checker import Checker


@pytest.mark.support(code="#CAM-9")
@pytest.mark.xfail(reason="Standalone method calls not implemented", strict=True)
def test_insert():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.insert(0, "A", [1, 2, 3])
df["A"]
"""
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert set(df.columns.keys()) == {"A"}
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-7")
def test_assign_create():
    code = """
import pandas as pd
df = pd.DataFrame({})
df = df.assign(A=[1, 2, 3])
df["A"]
"""
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert set(df.columns.keys()) == {"A"}
    assert len(fc.diagnostics) == 0


@pytest.mark.support(code="#CAM-7-1")
@pytest.mark.xfail(reason="Not implemented", strict=True)
def test_assign_subscript():
    code = """
import pandas as pd
df = pd.DataFrame({})
df.assign(A=[1, 2, 3])["A"]
"""
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert set(df.columns.keys()) == {"A"}
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
    fc = Checker.check(code)
    df = fc.dfs.get("df")
    assert df is not None
    assert set(df.columns.keys()) == {"A", "B"}
    assert len(fc.diagnostics) == 0
