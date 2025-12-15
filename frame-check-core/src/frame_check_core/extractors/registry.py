"""
Registry for column reference extractors.

To add a new extractor:
1. Write your extractor function in its own module
2. Import it below
3. Add it to the EXTRACTORS list in the order you want it tried

Extractors are tried in list order. The first one to return non-None wins.
"""
# ruff: noqa E402

import ast
from collections.abc import Callable

from frame_check_core.refs import ColumnRef

# Type alias for extractor functions
ExtractorFunc = Callable[[ast.expr], list[ColumnRef] | None]

# Import all extractors
from .binop import extract_column_refs_from_binop
from .column import extract_column_ref

# Extractors to use, in priority order (earlier = tried first)
EXTRACTORS: list[ExtractorFunc] = [
    extract_column_ref,  # df['col'] and df[['a', 'b']] - most common
    extract_column_refs_from_binop,  # df['A'] + df['B'] - binary operations
]


class Extractor:
    """
    Registry for column reference extractors.

    Extractors are simple functions that take an AST expression and return
    a list of ColumnRef objects if the expression matches their pattern,
    or None otherwise.

    Example:
        >>> import ast
        >>> expr = ast.parse("df['A'] + df['B']", mode="eval").body
        >>> refs = Extractor.extract(expr)
        >>> [ref.col_names[0] for ref in refs]
        ['A', 'B']
    """

    @classmethod
    def extract(cls, node: ast.expr) -> list[ColumnRef] | None:
        """
        Extract column references using registered extractors.

        Tries each extractor in EXTRACTORS order and returns the result
        from the first one that matches.

        Args:
            node: The AST expression to analyze.

        Returns:
            A list of ColumnRef objects if any extractor matches, None otherwise.

        Example:
            >>> import ast
            >>> expr = ast.parse("df['A'] + df['B']", mode="eval").body
            >>> refs = Extractor.extract(expr)
            >>> [ref.col_names[0] for ref in refs]
            ['A', 'B']
        """
        for extractor in EXTRACTORS:
            if refs := extractor(node):
                return refs

        return None

    @classmethod
    def get_registered(cls) -> list[ExtractorFunc]:
        """
        Get all registered extractors in order.

        Returns:
            List of extractor functions in the order they're tried.

        Example:
            >>> extractors = Extractor.get_registered()
            >>> len(extractors)
            2
        """
        return EXTRACTORS.copy()
