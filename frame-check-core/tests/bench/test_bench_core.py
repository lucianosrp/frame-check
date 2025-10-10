import pytest
from frame_check_core import FrameChecker


@pytest.mark.benchmark
def test_long_benchmark():
    FrameChecker.check("frame-check-core/tests/bench/long_pandas.py")
