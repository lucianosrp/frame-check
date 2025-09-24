def test_import_alias():

    from frame_check_core import FrameChecker

    code = """
    import pandas as pd
    """.strip()

    fc = FrameChecker.check(code)

    assert fc.import_aliases == {"pandas": "pd"}
