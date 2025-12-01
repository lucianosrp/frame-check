import ast

from frame_check_core.extractors.binop import extract_column_refs_from_binop


def test_binop():
    expr = ast.parse("df['amount'] + df['price']", mode="eval").body
    results = extract_column_refs_from_binop(expr)
    assert results is not None
    for expected_col, res in zip(["price", "amount"], results):
        assert res.df_name == "df"
        assert res.col_names == [expected_col]
