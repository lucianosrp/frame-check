"""
Extractor for DataFrame column references.

This module handles column access patterns:
- Single column: `df['col']`
- Multiple columns: `df[['a', 'b']]` (list form)

Example patterns matched:
    df['column_name']
    my_dataframe['A']
    data['price']
    df[['col1', 'col2', 'col3']]

Example patterns NOT matched:
    df[0]              # Integer index, not string
    df[variable]       # Variable, not constant string
    df['A']['B']       # Nested subscript
    df.column_name     # Attribute access, not subscript
    df['a', 'b']       # Tuple form (not standard pandas)
"""

import ast

from frame_check_core.refs import ColumnRef, is_constant, is_name, is_subscript

from .registry import Extractor

__all__ = ["extract_column_ref"]


@Extractor.register(priority=10, name="column_ref")
def extract_column_ref(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract a column reference from a subscript expression.

    Matches patterns:
    - `name['string']` - single column access
    - `name[['str1', 'str2', ...]]` - multi-column access (list form)

    Args:
        node: The AST expression to analyze.

    Returns:
        A list containing a single `ColumnRef` with the DataFrame name,
        column name(s), and AST node if the pattern matches; `None` otherwise.

    Example:
        >>> import ast
        >>> expr = ast.parse("df['amount']", mode="eval").body
        >>> refs = extract_column_ref(expr)
        >>> refs[0].df_name
        'df'
        >>> refs[0].col_names
        ['amount']

        >>> expr = ast.parse("df[['x', 'y', 'z']]", mode="eval").body
        >>> refs = extract_column_ref(expr)
        >>> refs[0].col_names
        ['x', 'y', 'z']
    """
    if not is_subscript(node):
        return None

    if not is_name(node.value):
        return None

    slice_node = node.slice

    # Single column: df['col']
    if is_constant(slice_node) and isinstance(slice_node.value, str):
        return [ColumnRef(node, node.value.id, [slice_node.value])]

    # Multi-column: df[['a', 'b']]
    if isinstance(slice_node, ast.List):
        col_names: list[str] = []
        for elt in slice_node.elts:
            if not isinstance(elt, ast.Constant):
                return None
            if not isinstance(elt.value, str):
                return None
            col_names.append(elt.value)

        if not col_names:
            return None

        return [ColumnRef(node, node.value.id, col_names)]

    return None


def extract_single_column_ref(node: ast.expr) -> ColumnRef | None:
    """
    Extract a single column reference from a subscript expression.

    This is a convenience function that returns a single ColumnRef instead
    of a list. Useful when you know you're dealing with a simple column
    access pattern.

    Args:
        node: The AST expression to analyze.

    Returns:
        A `ColumnRef` if the pattern matches, `None` otherwise.

    Example:
        >>> import ast
        >>> expr = ast.parse("df['amount']", mode="eval").body
        >>> ref = extract_single_column_ref(expr)
        >>> ref.df_name
        'df'
        >>> ref.col_names
        ['amount']
    """
    refs = extract_column_ref(node)
    return refs[0] if refs else None
