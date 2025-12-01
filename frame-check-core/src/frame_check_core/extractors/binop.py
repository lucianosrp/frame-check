"""
Extractor for binary operation expressions containing column references.

This module handles expressions where DataFrame columns are combined using
binary operators like `+`, `-`, `*`, `/`, etc. It recursively traverses
the binary operation tree to find all column references.

Example patterns matched:
    df['A'] + df['B']
    df['price'] * df['quantity']
    df['A'] + df['B'] - df['C']
    (df['A'] + df['B']) * df['C']

Example patterns NOT matched:
    df['A'] + 1              # Constant operand, not column reference
    df['A'] + some_variable  # Variable operand
    df['A'].sum()            # Method call, not binary operation

Note:
    This extractor requires ALL operands in the expression to be column
    references. If any operand is not a recognized column reference
    (e.g., a constant or variable), the entire expression returns None.
"""

import ast

from frame_check_core.refs import ColumnRef, is_binop

from .column import extract_single_column_ref
from .registry import Extractor

__all__ = ["extract_column_refs_from_binop"]


@Extractor.register(priority=20, name="binop")
def extract_column_refs_from_binop(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract all column references from a binary operation tree.

    Recursively traverses a `BinOp` AST node, collecting all column
    references from both sides of each operation. The traversal handles
    nested binary operations (e.g., `df['A'] + df['B'] + df['C']`).

    Args:
        node: The AST expression to analyze.

    Returns:
        A list of `ColumnRef` objects for all columns found in the expression,
        or `None` if:
        - The node is not a `BinOp`
        - Any operand is not a valid column reference
        - The expression contains no column references

    Example:
        >>> import ast
        >>> expr = ast.parse("df['A'] + df['B']", mode="eval").body
        >>> refs = extract_column_refs_from_binop(expr)
        >>> [ref.col_names[0] for ref in refs]
        ['B', 'A']
    """
    if not is_binop(node):
        return None

    refs: list[ColumnRef] = []
    stack = [node.left, node.right]

    while stack:
        n = stack.pop()
        if is_binop(n):
            stack.extend([n.left, n.right])
        elif ref := extract_single_column_ref(n):
            refs.append(ref)
        else:
            return None  # Non-column operand in expression

    return refs if refs else None
