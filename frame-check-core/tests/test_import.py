def test_import_alias():
    import ast

    from frame_check_core import FrameChecker

    code = """
    import pandas as pd
    """.strip()

    tree = ast.parse(code)
    fc = FrameChecker()
    fc.visit(tree)

    assert fc.import_aliases == {"pandas": "pd"}
