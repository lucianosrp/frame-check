"""Tests for the Extractor registry."""

import ast

import pytest
from frame_check_core.extractors.registry import Extractor
from frame_check_core.refs import ColumnRef


@pytest.fixture(autouse=True)
def clean_registry():
    """Save and restore the registry state around each test."""
    # Save the current registry state
    original_registry = Extractor._registry.copy()
    original_sorted = Extractor._sorted

    yield

    # Restore the registry state
    Extractor._registry = original_registry
    Extractor._sorted = original_sorted


# --- Extractor Registration Tests ---


def test_register_extractor():
    """Test basic extractor registration."""

    @Extractor.register(priority=50)
    def my_extractor(node: ast.expr) -> list[ColumnRef] | None:
        return None

    registered = Extractor.get_registered()
    names = [name for _, name, _ in registered]
    assert "my_extractor" in names


def test_register_with_custom_name():
    """Test registration with custom name."""

    @Extractor.register(priority=50, name="custom_name")
    def some_extractor(node: ast.expr) -> list[ColumnRef] | None:
        return None

    registered = Extractor.get_registered()
    names = [name for _, name, _ in registered]
    assert "custom_name" in names
    assert "some_extractor" not in names


def test_priority_ordering():
    """Test that extractors are ordered by priority."""
    Extractor.clear()

    @Extractor.register(priority=30, name="third")
    def ext3(node: ast.expr) -> list[ColumnRef] | None:
        return None

    @Extractor.register(priority=10, name="first")
    def ext1(node: ast.expr) -> list[ColumnRef] | None:
        return None

    @Extractor.register(priority=20, name="second")
    def ext2(node: ast.expr) -> list[ColumnRef] | None:
        return None

    registered = Extractor.get_registered()
    names = [name for _, name, _ in registered]
    assert names == ["first", "second", "third"]


def test_default_priority():
    """Test that default priority is 50."""
    Extractor.clear()

    @Extractor.register(name="default_priority")
    def ext_default(node: ast.expr) -> list[ColumnRef] | None:
        return None

    registered = Extractor.get_registered()
    priorities = [
        priority for priority, name, _ in registered if name == "default_priority"
    ]
    assert priorities == [50]


# --- Extractor Extract Tests ---


def test_extract_returns_first_match():
    """Test that extract returns the first matching extractor's result."""
    Extractor.clear()

    @Extractor.register(priority=10, name="always_none")
    def ext_none(node: ast.expr) -> list[ColumnRef] | None:
        return None

    @Extractor.register(priority=20, name="always_match")
    def ext_match(node: ast.expr) -> list[ColumnRef] | None:
        # Create a dummy ColumnRef
        if isinstance(node, ast.Subscript):
            return [ColumnRef(node, "test", ["col"])]
        return None

    @Extractor.register(priority=30, name="never_reached")
    def ext_never(node: ast.expr) -> list[ColumnRef] | None:
        raise AssertionError("This should never be called")

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is not None
    assert len(refs) == 1
    assert refs[0].df_name == "test"


def test_extract_returns_none_when_no_match():
    """Test that extract returns None when no extractor matches."""
    Extractor.clear()

    @Extractor.register(priority=10, name="no_match")
    def ext_no_match(node: ast.expr) -> list[ColumnRef] | None:
        return None

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is None


def test_extract_with_empty_registry():
    """Test extract with no registered extractors."""
    Extractor.clear()

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is None


# --- Extractor Management Tests ---


def test_clear():
    """Test clearing the registry."""
    Extractor.clear()

    @Extractor.register(priority=10, name="to_clear")
    def ext(node: ast.expr) -> list[ColumnRef] | None:
        return None

    assert len(Extractor.get_registered()) > 0

    Extractor.clear()

    assert len(Extractor.get_registered()) == 0


def test_unregister_existing():
    """Test unregistering an existing extractor."""
    Extractor.clear()

    @Extractor.register(priority=10, name="to_remove")
    def ext(node: ast.expr) -> list[ColumnRef] | None:
        return None

    assert Extractor.unregister("to_remove") is True
    names = [name for _, name, _ in Extractor.get_registered()]
    assert "to_remove" not in names


def test_unregister_nonexistent():
    """Test unregistering a non-existent extractor."""
    Extractor.clear()

    assert Extractor.unregister("nonexistent") is False


def test_get_registered_returns_sorted_by_priority():
    """Test that get_registered returns the extractors sorted by priority."""
    Extractor.clear()

    @Extractor.register(priority=20, name="second")
    def ext2(node: ast.expr) -> list[ColumnRef] | None:
        return None

    @Extractor.register(priority=10, name="first")
    def ext1(node: ast.expr) -> list[ColumnRef] | None:
        return None

    registered = Extractor.get_registered()

    # Verify ordering
    assert registered[0][0] == 10
    assert registered[0][1] == "first"
    assert registered[1][0] == 20
    assert registered[1][1] == "second"


# --- Built-in Extractors Tests ---


def test_builtin_extractors_registered():
    """Test that the built-in extractors are registered."""
    registered = Extractor.get_registered()
    names = [name for _, name, _ in registered]

    assert "column_ref" in names
    assert "binop" in names


def test_column_ref_has_lower_priority_than_binop():
    """Test that column_ref has lower priority than binop."""
    registered = Extractor.get_registered()
    priorities = {name: priority for priority, name, _ in registered}

    assert priorities["column_ref"] < priorities["binop"]


def test_builtin_extractor_single_column():
    """Test that built-in extractors work for single column access."""
    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)
    assert refs is not None
    assert len(refs) == 1
    assert refs[0].col_names == ["A"]


def test_builtin_extractor_binary_operation():
    """Test that built-in extractors work for binary operations."""
    expr = ast.parse("df['A'] + df['B']", mode="eval").body
    refs = Extractor.extract(expr)
    assert refs is not None
    assert len(refs) == 2
    col_names = {refs[0].col_names[0], refs[1].col_names[0]}
    assert col_names == {"A", "B"}
