from frame_check_core.checker import Checker


def test_import_alias():
    code = """
import pandas as pd
    """.strip()

    fc = Checker.check(code)

    assert fc.pandas_aliases == {"pd"}


def test_import_full():
    code = """
import pandas
    """.strip()

    fc = Checker.check(code)

    assert fc.pandas_aliases == {"pandas"}
