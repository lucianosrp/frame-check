"""
Registry for column reference extractors.

This module provides a registry pattern for extractors, similar to the PD and DF
registries for pandas functions and DataFrame methods. Extractors can be registered
using the `@Extractor.register()` decorator with an optional priority.

Usage:
    from frame_check_core.extractors.registry import Extractor

    @Extractor.register(priority=10)
    def extract_my_pattern(node: ast.expr) -> list[ColumnRef] | None:
        # Extract column references from your pattern
        ...

    # The extractor is automatically included in extract()
    refs = Extractor.extract(some_node)

Priority:
    Lower priority numbers are tried first. Default priority is 50.
    Suggested ranges:
    - 0-19: Fast, common patterns (e.g., simple column access)
    - 20-39: Moderately common patterns (e.g., binary operations)
    - 40-59: Less common patterns (e.g., method calls)
    - 60-79: Rare patterns
    - 80-99: Fallback/catch-all patterns
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass, field

from frame_check_core.refs import ColumnRef

# Type alias for extractor functions
ExtractorFunc = Callable[[ast.expr], list[ColumnRef] | None]


@dataclass(order=True, slots=True)
class _RegisteredExtractor:
    """Internal class to hold an extractor with its priority."""

    priority: int
    name: str = field(compare=False)
    func: ExtractorFunc = field(compare=False)


class Extractor:
    """
    Registry for column reference extractors.

    Extractors are functions that take an AST expression and return a list of
    ColumnRef objects if the expression matches their pattern, or None otherwise.

    The registry maintains extractors sorted by priority, allowing efficient
    pattern matching by trying the most common patterns first.

    Example:
        @Extractor.register(priority=10)
        def extract_column_ref(node: ast.expr) -> list[ColumnRef] | None:
            # Handle df['col'] pattern
            ...

        @Extractor.register(priority=20)
        def extract_binop(node: ast.expr) -> list[ColumnRef] | None:
            # Handle df['A'] + df['B'] pattern
            ...

        # Extract refs using all registered extractors
        refs = Extractor.extract(some_ast_node)
    """

    _registry: list[_RegisteredExtractor] = []
    _sorted: bool = True

    @classmethod
    def register(
        cls, priority: int = 50, *, name: str | None = None
    ) -> Callable[[ExtractorFunc], ExtractorFunc]:
        """
        Decorator to register an extractor function.

        Args:
            priority: Extraction priority (lower = tried first). Default is 50.
            name: Optional name for the extractor. Defaults to function name.

        Returns:
            Decorator function that registers the extractor.

        Example:
            @Extractor.register(priority=10)
            def my_extractor(node: ast.expr) -> list[ColumnRef] | None:
                ...

            @Extractor.register(priority=20, name="binop_extractor")
            def extract_binop(node: ast.expr) -> list[ColumnRef] | None:
                ...
        """

        def decorator(func: ExtractorFunc) -> ExtractorFunc:
            extractor_name = name if name is not None else func.__name__
            registered = _RegisteredExtractor(
                priority=priority,
                name=extractor_name,
                func=func,
            )
            cls._registry.append(registered)
            cls._sorted = False
            return func

        return decorator

    @classmethod
    def _ensure_sorted(cls) -> None:
        """Ensure the registry is sorted by priority."""
        if not cls._sorted:
            cls._registry.sort()
            cls._sorted = True

    @classmethod
    def extract(cls, node: ast.expr) -> list[ColumnRef] | None:
        """
        Extract column references using all registered extractors.

        Tries each extractor in priority order and returns the result from
        the first one that matches (returns non-None).

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
        cls._ensure_sorted()

        for registered in cls._registry:
            if refs := registered.func(node):
                return refs

        return None

    @classmethod
    def get_registered(cls) -> list[tuple[int, str, ExtractorFunc]]:
        """
        Get all registered extractors with their priorities.

        Returns:
            List of (priority, name, function) tuples, sorted by priority.

        Example:
            >>> for priority, name, func in Extractor.get_registered():
            ...     print(f"{priority}: {name}")
            10: extract_column_ref
            20: extract_binop
        """
        cls._ensure_sorted()
        return [(r.priority, r.name, r.func) for r in cls._registry]

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered extractors.

        Primarily useful for testing.
        """
        cls._registry.clear()
        cls._sorted = True

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister an extractor by name.

        Args:
            name: The name of the extractor to remove.

        Returns:
            True if the extractor was found and removed, False otherwise.

        Example:
            >>> Extractor.unregister("my_extractor")
            True
        """
        for i, registered in enumerate(cls._registry):
            if registered.name == name:
                cls._registry.pop(i)
                return True
        return False
