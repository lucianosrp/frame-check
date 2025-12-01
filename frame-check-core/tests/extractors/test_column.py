import ast

from frame_check_core.extractors.column import (
    extract_column_ref,
    extract_single_column_ref,
)


def test_extract_column_ref_single_column_ref():
    expr = ast.parse("df['amount']", mode="eval").body
    res = extract_column_ref(expr)
    assert res is not None
    assert len(res) == 1
    assert res[0].df_name == "df"
    assert res[0].col_names == ["amount"]


def test_extract_column_ref_list_column_ref():
    expr = ast.parse("df[['amount', 'price']]", mode="eval").body
    res = extract_column_ref(expr)
    assert res is not None
    assert len(res) == 1
    assert res[0].df_name == "df"
    assert res[0].col_names == ["amount", "price"]


def test_extract_column_ref_non_subscript_returns_none():
    expr = ast.parse("df.column", mode="eval").body
    res = extract_column_ref(expr)
    assert res is None


def test_extract_column_ref_integer_subscript_returns_none():
    expr = ast.parse("df[0]", mode="eval").body
    res = extract_column_ref(expr)
    assert res is None


def test_extract_column_ref_variable_subscript_returns_none():
    expr = ast.parse("df[col_name]", mode="eval").body
    res = extract_column_ref(expr)
    assert res is None


# Tests for extract_single_column_ref which returns a single ColumnRef.


def test_extract_single_column_ref_single_column_ref():
    expr = ast.parse("df['amount']", mode="eval").body
    res = extract_single_column_ref(expr)
    assert res is not None
    assert res.df_name == "df"
    assert res.col_names == ["amount"]


def test_extract_single_column_ref_list_column_ref():
    expr = ast.parse("df[['amount', 'price']]", mode="eval").body
    res = extract_single_column_ref(expr)
    assert res is not None
    assert res.df_name == "df"
    assert res.col_names == ["amount", "price"]


def test_extract_single_column_ref_non_subscript_returns_none():
    expr = ast.parse("df.column", mode="eval").body
    res = extract_single_column_ref(expr)
    assert res is None


def test_extract_single_column_ref_integer_subscript_returns_none():
    expr = ast.parse("df[0]", mode="eval").body
    res = extract_single_column_ref(expr)
    assert res is None
