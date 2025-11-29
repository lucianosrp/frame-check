from pathlib import Path

import pytest
from frame_check_core.checker import Checker


@pytest.mark.benchmark
def test_long_benchmark():
    benchmark_file = Path(__file__).parent / "long_pandas.py"
    Checker.check(benchmark_file)
