from frame_check_core import FrameChecker
from frame_check_core.models.region import CodePosition, CodeRegion


def test_frame_init_dict_arg():
    code = """
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=4, col=0),
        end=CodePosition(row=4, col=1),
    )


def test_frame_init_list_of_dict_arg():
    code = """
import pandas as pd

df = pd.DataFrame([{"a": 1, "b": 4 }, {"a": 2, "b": 5 }, {"a": 3, "b": 6 }])
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(4, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=4, col=0),
        end=CodePosition(row=4, col=1),
    )


def test_frame_init_dict_var_arg():
    code = """
import pandas as pd

data = {"a": [1, 2, 3], "b": [4, 5, 6]}
df = pd.DataFrame(data)
"""
    fc = FrameChecker.check(code)
    assert fc.frames.instance_keys() == ["df"]
    frame_instance = fc.frames.get_at(5, "df")
    assert frame_instance is not None
    assert frame_instance.id == "df"
    assert frame_instance.columns == ["a", "b"]
    assert frame_instance.region == CodeRegion(
        start=CodePosition(row=5, col=0),
        end=CodePosition(row=5, col=1),
    )
