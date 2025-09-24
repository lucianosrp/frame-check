import ast

from frame_check_core import FrameChecker


def test_frame_init_dict_arg():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""
    fc = FrameChecker()
    tree = ast.parse(code)
    fc.visit(tree)
    assert fc.frames.frame_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b"]
    assert frame_instance.lineno == 4


def test_frame_init_dict_var_arg():
    code = """
import pandas as pd

data = {"a": [1, 2, 3], "b": [4, 5, 6]}
df = pd.DataFrame(data)
"""
    fc = FrameChecker()
    tree = ast.parse(code)
    fc.visit(tree)
    assert fc.frames.frame_keys() == ["df"]
    frame_instance = fc.frames.get_at(5, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b"]
    assert frame_instance.lineno == 5
