"""
Extractors for identifying DataFrame column references in Python AST.

This package provides a unified interface for extracting column references
from various AST expression patterns. Each extractor handles a specific
pattern type (simple subscripts, binary operations, method calls, etc.)
and returns structured `ColumnRef` objects.

Usage:
    The main entry point is `Extractor.extract()`, which tries all registered
    extractors in priority order and returns the first successful match:

    >>> from frame_check_core.extractors import Extractor
    >>> import ast
    >>> expr = ast.parse("df['A'] + df['B']", mode="eval").body
    >>> refs = Extractor.extract(expr)
    >>> [ref.col_names[0] for ref in refs]
    ['A', 'B']

    For specific patterns, individual extractors can be used directly:

    >>> from frame_check_core.extractors import extract_column_ref
    >>> expr = ast.parse("df['amount']", mode="eval").body
    >>> refs = extract_column_ref(expr)
    >>> refs[0].col_names
    ['amount']

Adding new extractors:
    Use the `@Extractor.register()` decorator:

    >>> from frame_check_core.extractors import Extractor
    >>> from frame_check_core.refs import ColumnRef
    >>>
    >>> @Extractor.register(priority=30, name="my_pattern")
    ... def extract_my_pattern(node: ast.expr) -> list[ColumnRef] | None:
    ...     # Extract column references from your pattern
    ...     ...

Priority:
    Lower priority numbers are tried first. Suggested ranges:
    - 0-19: Fast, common patterns (e.g., simple column access)
    - 20-39: Moderately common patterns (e.g., binary operations)
    - 40-59: Less common patterns (e.g., method calls)
    - 60-79: Rare patterns
    - 80-99: Fallback/catch-all patterns
"""

import ast

from frame_check_core.refs import ColumnRef

from .binop import extract_column_refs_from_binop

# Import extractors to trigger their registration
from .column import extract_column_ref, extract_single_column_ref
from .registry import Extractor

__all__ = [
    # Registry
    "Extractor",
    # Types
    "ColumnRef",
    # Individual extractors (for direct use)
    "extract_column_ref",
    "extract_single_column_ref",
    "extract_column_refs_from_binop",
    "extract",
]


def extract(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract column references from any recognized RHS expression pattern.

    This function is sugar-coating for `Extractor.extract()`
    which tries all registered extractors in priority order.

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
        >>> refs = extract(expr)
        >>> len(refs)
        1
        >>> refs[0].col_names
        ['A']

        >>> # Binary operation
        >>> expr = ast.parse("df['A'] * df['B']", mode="eval").body
        >>> refs = extract(expr)
        >>> sorted(ref.col_names[0] for ref in refs)
        ['A', 'B']

        >>> # Unsupported pattern
        >>> expr = ast.parse("df['A'] + 1", mode="eval").body
        >>> extract(expr) is None
        True
    """
    return Extractor.extract(node)
