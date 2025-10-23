import ast

import pytest
from frame_check_core.models.history import FrameInstance, get_column_values


@pytest.mark.parametrize(
    "col,expected",
    [
        ("col_a", ["col_a"]),
        (["col_a"], ["col_a"]),
        (["col_a", "col_b"], ["col_a", "col_b"]),
        (("col_a", "col_b"), ["col_a", "col_b"]),
        ({"col_a", "col_b"}, ["col_a", "col_b"]),
        (ast.Constant(value="value"), ["value"]),
        (
            ast.List(elts=[ast.Constant(value="value"), ast.Constant(value="value2")]),
            ["value", "value2"],
        ),
        (
            ast.List(
                elts=[
                    ast.Constant(value="value"),
                    ast.List(
                        elts=[
                            ast.Constant(value="value2"),
                            ast.Constant(value="value3"),
                        ]
                    ),
                ]
            ),
            ["value", "value2", "value3"],
        ),
    ],
)
def test_get_column_values(col, expected):
    assert sorted(get_column_values(col)) == sorted(expected)


@pytest.mark.parametrize(
    "columns,expected",
    [
        ("col_a", {"col_a"}),
        (["col_a"], {"col_a"}),
        (["col_a", "col_b"], {"col_a", "col_b"}),
        (ast.Constant(value="value"), {"value"}),
        (
            ast.List(elts=[ast.Constant(value="value"), ast.Constant(value="value2")]),
            {"value", "value2"},
        ),
    ],
)
def test_frame_instance_new(columns, expected):
    frame = FrameInstance.new(
        lineno=10,
        id="df",
        data_arg=None,
        keywords=[],
        columns=columns,
    )
    assert frame.lineno == 10
    assert frame.id == "df"
    assert frame.data_arg is None
    assert frame.keywords == []
    assert frame.columns == expected


def test_frame_instance_from_frame():
    original_frame = FrameInstance.new(
        lineno=10,
        id="df",
        data_arg=None,
        keywords=[],
        columns=["col_a", "col_b"],
    )

    new_frame = original_frame.new_instance(lineno=11, new_columns=["col_c", "col_d"])

    assert new_frame.id == original_frame.id
    assert new_frame.data_arg is original_frame.data_arg
    assert new_frame.keywords == original_frame.keywords
    assert new_frame.columns == {"col_a", "col_b", "col_c", "col_d"}
