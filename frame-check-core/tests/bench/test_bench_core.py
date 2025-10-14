import pytest
from frame_check_core import FrameChecker
from pathlib import Path


@pytest.mark.benchmark
def test_long_benchmark():
    benchmark_file = Path(__file__).parent / "long_pandas.py"
    FrameChecker.check(benchmark_file)
