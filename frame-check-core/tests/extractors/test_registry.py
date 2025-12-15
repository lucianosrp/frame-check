"""Tests for the Extractor registry."""

import ast

import pytest
from frame_check_core.extractors.registry import EXTRACTORS, Extractor
from frame_check_core.refs import ColumnRef


@pytest.fixture(autouse=True)
def clean_registry():
    """Save and restore the registry state around each test."""
    # Save the current registry state
    original_extractors = EXTRACTORS.copy()

    yield

    # Restore the registry state
    EXTRACTORS.clear()
    EXTRACTORS.extend(original_extractors)


def _clear_registry():
    """Helper to clear the registry for tests that need an empty state."""
    EXTRACTORS.clear()


def _set_registry(extractors):
    """Helper to set the registry to a specific list of extractors."""
    EXTRACTORS.clear()
    EXTRACTORS.extend(extractors)


# --- Extractor Extract Tests ---


def test_extract_returns_first_match():
    """Test that extract returns the first matching extractor's result."""

    def ext_none(node: ast.expr) -> list[ColumnRef] | None:
        return None

    def ext_match(node: ast.expr) -> list[ColumnRef] | None:
        # Create a dummy ColumnRef
        if isinstance(node, ast.Subscript):
            return [ColumnRef(node, "test", ["col"])]
        return None

    def ext_never(node: ast.expr) -> list[ColumnRef] | None:
        raise AssertionError("This should never be called")

    _set_registry([ext_none, ext_match, ext_never])

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is not None
    assert len(refs) == 1
    assert refs[0].df_name == "test"


def test_extract_returns_none_when_no_match():
    """Test that extract returns None when no extractor matches."""

    def ext_no_match(node: ast.expr) -> list[ColumnRef] | None:
        return None

    _set_registry([ext_no_match])

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is None


def test_extract_with_empty_registry():
    """Test extract with no registered extractors."""
    _clear_registry()

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    assert refs is None


def test_get_registered_returns_list():
    """Test that get_registered returns the list of extractors."""

    def ext1(node: ast.expr) -> list[ColumnRef] | None:
        return None

    def ext2(node: ast.expr) -> list[ColumnRef] | None:
        return None

    _set_registry([ext1, ext2])

    registered = Extractor.get_registered()

    # Verify we get a list of functions
    assert len(registered) == 2
    assert registered[0] == ext1
    assert registered[1] == ext2


def test_ordering_matters():
    """Test that extractors are tried in list order."""

    def first_extractor(node: ast.expr) -> list[ColumnRef] | None:
        if isinstance(node, ast.Subscript):
            return [ColumnRef(node, "first", ["col"])]
        return None

    def second_extractor(node: ast.expr) -> list[ColumnRef] | None:
        if isinstance(node, ast.Subscript):
            return [ColumnRef(node, "second", ["col"])]
        return None

    _set_registry([first_extractor, second_extractor])

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)

    # Should get result from first extractor
    assert refs is not None
    assert refs[0].df_name == "first"

    # Reverse the order
    _set_registry([second_extractor, first_extractor])

    refs = Extractor.extract(expr)

    # Should now get result from second extractor (which is now first)
    assert refs is not None
    assert refs[0].df_name == "second"


# --- Built-in Extractors Tests ---


def test_builtin_extractors_registered():
    """Test that the built-in extractors are registered."""
    # Restore original registry for this test
    from frame_check_core.extractors.binop import extract_column_refs_from_binop
    from frame_check_core.extractors.column import extract_column_ref

    _set_registry([extract_column_ref, extract_column_refs_from_binop])

    registered = Extractor.get_registered()

    assert extract_column_ref in registered
    assert extract_column_refs_from_binop in registered


def test_column_ref_comes_before_binop():
    """Test that column_ref comes before binop in the list."""
    # Restore original registry for this test
    from frame_check_core.extractors.binop import extract_column_refs_from_binop
    from frame_check_core.extractors.column import extract_column_ref

    _set_registry([extract_column_ref, extract_column_refs_from_binop])

    registered = Extractor.get_registered()

    column_ref_idx = registered.index(extract_column_ref)
    binop_idx = registered.index(extract_column_refs_from_binop)

    assert column_ref_idx < binop_idx


def test_builtin_extractor_single_column():
    """Test that built-in extractors work for single column access."""
    # Restore original registry for this test
    from frame_check_core.extractors.binop import extract_column_refs_from_binop
    from frame_check_core.extractors.column import extract_column_ref

    _set_registry([extract_column_ref, extract_column_refs_from_binop])

    expr = ast.parse("df['A']", mode="eval").body
    refs = Extractor.extract(expr)
    assert refs is not None
    assert len(refs) == 1
    assert refs[0].col_names == ["A"]


def test_builtin_extractor_binary_operation():
    """Test that built-in extractors work for binary operations."""
    # Restore original registry for this test
    from frame_check_core.extractors.binop import extract_column_refs_from_binop
    from frame_check_core.extractors.column import extract_column_ref

    _set_registry([extract_column_ref, extract_column_refs_from_binop])

    expr = ast.parse("df['A'] + df['B']", mode="eval").body
    refs = Extractor.extract(expr)
    assert refs is not None
    assert len(refs) == 2
    col_names = {refs[0].col_names[0], refs[1].col_names[0]}
    assert col_names == {"A", "B"}
