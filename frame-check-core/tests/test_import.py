def test_import_alias():
    from frame_check_core.frame_checker import FrameChecker

    code = """
    import pandas as pd
    """.strip()

    fc = FrameChecker.check(code)

    assert fc.import_aliases == {"pandas": "pd"}


def test_import_full():
    from frame_check_core.frame_checker import FrameChecker

    code = """
    import pandas
    """.strip()

    fc = FrameChecker.check(code)

    assert fc.import_aliases == {"pandas": "pandas"}
