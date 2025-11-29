"""
Extractors for identifying DataFrame column references in Python AST.

This package provides a unified interface for extracting column references
from various AST expression patterns. Each extractor handles a specific
pattern type (simple subscripts, binary operations, method calls, etc.)
and returns structured `ColumnRef` objects.

Usage:
    The main entry point is `extract_value_refs`, which tries all available
    extractors in sequence and returns the first successful match:

    >>> from frame_check_core.dev.extractors import extract_value_refs
    >>> import ast
    >>> expr = ast.parse("df['A'] + df['B']", mode="eval").body
    >>> refs = extract_value_refs(expr)
    >>> [ref.col_names[0] for ref in refs]
    ['B', 'A']

    For specific patterns, individual extractors can be used directly:

    >>> from frame_check_core.dev.extractors import extract_column_ref
    >>> expr = ast.parse("df['amount']", mode="eval").body
    >>> ref = extract_column_ref(expr)
    >>> ref.col_names
    ['amount']

Available extractors:
    - `extract_column_ref`: Single `df['col']` or multi-column `df[['a', 'b']]` patterns
    - `extract_column_refs_from_binop`: Binary operations like `df['A'] + df['B']`

Adding new extractors:
    1. Create a new module in this package (e.g., `method.py`)
    2. Implement an extractor function returning `list[ColumnRef] | None`
    3. Import and add it to `extract_value_refs` in this file
    4. Export it in `__all__`
"""

import ast

from frame_check_core.refs import ColumnRef

from .binop import extract_column_refs_from_binop
from .column import extract_column_ref

__all__ = [
    "ColumnRef",
    "extract_column_ref",
    "extract_column_refs_from_binop",
    "extract_value_refs",
]


def extract_value_refs(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract column references from any recognized RHS expression pattern.

    This is the main entry point for column reference extraction. It tries
    each available extractor in order of likelihood and returns the first
    successful match.

    The extraction order is optimized for common patterns:
    1. Simple column reference (`df['A']`) - most common
    2. Binary operations (`df['A'] + df['B']`) - common in assignments
    3. (Future) Method calls (`df['A'].fillna(df['B'])`)

    Args:
        node: The AST expression to analyze (typically the RHS of an assignment).

    Returns:
        A list of `ColumnRef` objects if the pattern is recognized.
        Returns `None` if:
        - The expression doesn't match any known pattern
        - The expression contains unsupported operands (e.g., constants, variables)

    Example:
        >>> import ast
        >>> # Simple column reference
        >>> expr = ast.parse("df['A']", mode="eval").body
        >>> refs = extract_value_refs(expr)
        >>> len(refs)
        1
        >>> refs[0].col_names
        ['A']

        >>> # Binary operation
        >>> expr = ast.parse("df['A'] * df['B']", mode="eval").body
        >>> refs = extract_value_refs(expr)
        >>> sorted(ref.col_names[0] for ref in refs)
        ['A', 'B']

        >>> # Unsupported pattern
        >>> expr = ast.parse("df['A'] + 1", mode="eval").body
        >>> extract_value_refs(expr) is None
        True
    """
    # Fast path: single column reference (most common case)
    # Example: df['A'] = df['B']
    if ref := extract_column_ref(node):
        return [ref]

    # BinOp chains: df['A'] + df['B'], df['A'] * df['B'] + df['C'], etc.
    if refs := extract_column_refs_from_binop(node):
        return refs

    # Future: Method calls like df['A'].fillna(df['B'])
    # if refs := extract_column_refs_from_method(node):
    #     return refs

    return None
