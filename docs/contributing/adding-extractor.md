# Adding an Extractor

This guide shows how to add a new extractor to recognize column reference patterns in Python code.

## Overview

Extractors identify DataFrame column references in various AST expression patterns. Each extractor handles a specific pattern type and returns `ColumnRef` objects that the checker uses for validation.

**Location**: `frame-check-core/src/frame_check_core/extractors/`

## When to Add an Extractor

Add a new extractor when you want to track column references in a pattern that isn't currently recognized.

## The Pattern

```python
import ast
from frame_check_core.refs import ColumnRef

def extract_column_refs_from_X(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract column references from pattern X.
    
    Returns:
        List of ColumnRef objects if pattern matches, None otherwise.
    """
    # 1. Check if node matches your pattern
    if not isinstance(node, ast.SomeType):
        return None
    
    # 2. Extract column references
    refs = []
    # ... extraction logic ...
    
    # 3. Return refs or None
    return refs if refs else None
```

### Return Type

- `list[ColumnRef]`: Pattern matched, here are the column references found
- `None`: Pattern didn't match, try the next extractor

### The `ColumnRef` Dataclass

```python
@dataclass(slots=True)
class ColumnRef:
    node: ast.Subscript    # Original AST node for location tracking
    df_name: str           # DataFrame variable name (e.g., 'df')
    col_names: list[str]   # Column names being accessed (e.g., ['A'])
```

## Example: Existing `extract_column_ref`

The simplest extractor handles `df['col']` patterns:

```python
def extract_column_ref(node: ast.expr) -> ColumnRef | None:
    if not is_subscript(node):
        return None

    if not is_name(node.value):
        return None

    slice_node = node.slice

    # Single column: df['col']
    if is_constant(slice_node) and isinstance(slice_node.value, str):
        return ColumnRef(node, node.value.id, [slice_node.value])

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

        return ColumnRef(node, node.value.id, col_names)

    return None
```

## Example: Existing `extract_column_refs_from_binop`

Handles binary operations like `df['A'] + df['B']`:

```python
def extract_column_refs_from_binop(node: ast.expr) -> list[ColumnRef] | None:
    if not is_binop(node):
        return None

    refs: list[ColumnRef] = []
    stack = [node.left, node.right]

    while stack:
        n = stack.pop()
        if is_binop(n):
            # Nested binop: recurse into both sides
            stack.extend([n.left, n.right])
        elif ref := extract_column_ref(n):
            refs.append(ref)
        else:
            # Non-column operand (e.g., constant) - pattern doesn't match
            return None

    return refs if refs else None
```

## Step-by-Step: Adding a Method Call Extractor

Let's add support for `df['A'].fillna(df['B'])`.

### Step 1: Create the module

Create `frame-check-core/src/frame_check_core/extractors/method.py`:

```python
"""
Extractor for method call expressions containing column references.

Handles patterns like:
    df['A'].fillna(df['B'])
    df['A'].replace(df['B'], df['C'])
    df['A'].where(df['B'] > 0)

Does NOT handle:
    df.groupby('A')          # Method on DataFrame, not column
    df['A'].sum()            # No column refs in arguments
"""

import ast

from frame_check_core.refs import ColumnRef, is_call, is_attribute

from .column import extract_column_ref

__all__ = ["extract_column_refs_from_method"]


def extract_column_refs_from_method(node: ast.expr) -> list[ColumnRef] | None:
    """
    Extract column references from a method call on a column.
    
    Matches: df['col'].method(...) where args may contain column refs.
    
    Args:
        node: The AST expression to analyze.
        
    Returns:
        List of ColumnRef objects for all columns found, or None if
        the pattern doesn't match.
    """
    # Must be a Call node: something(...)
    if not is_call(node):
        return None
    
    # func must be an Attribute: something.method
    if not is_attribute(node.func):
        return None
    
    # The object being called on should be a column ref: df['col'].method
    base_ref = extract_column_ref(node.func.value)
    if base_ref is None:
        return None
    
    refs = [base_ref]
    
    # Check positional args for additional column references
    for arg in node.args:
        if arg_ref := extract_column_ref(arg):
            refs.append(arg_ref)
    
    # Check keyword args too
    for kw in node.keywords:
        if kw_ref := extract_column_ref(kw.value):
            refs.append(kw_ref)
    
    return refs
```

### Step 2: Register the extractor

Update `frame-check-core/src/frame_check_core/extractors/__init__.py`:

```py hl_lines="6 12 26-28"
import ast
from frame_check_core.refs import ColumnRef

from .binop import extract_column_refs_from_binop
from .column import extract_column_ref
from .method import extract_column_refs_from_method  # ADD THIS

__all__ = [
    "ColumnRef",
    "extract_column_ref",
    "extract_column_refs_from_binop",
    "extract_column_refs_from_method",  # ADD THIS
    "extract_value_refs",
]


def extract_value_refs(node: ast.expr) -> list[ColumnRef] | None:
    # Fast path: single column reference (most common case)
    if ref := extract_column_ref(node):
        return [ref]

    # BinOp chains: df['A'] + df['B']
    if refs := extract_column_refs_from_binop(node):
        return refs

    # Method calls: df['A'].fillna(df['B'])  # ADD THIS
    if refs := extract_column_refs_from_method(node):
        return refs

    return None
```

### Step 3: Add tests

Create `frame-check-core/tests/test_extractor_method.py`:

```python
"""Tests for the method call extractor."""

import ast
import pytest
from frame_check_core.extractors import extract_column_refs_from_method


def parse_expr(code: str) -> ast.expr:
    """Helper to parse a single expression."""
    return ast.parse(code, mode="eval").body


def test_fillna_with_column():
    expr = parse_expr("df['A'].fillna(df['B'])")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is not None
    assert len(refs) == 2
    assert {r.col_names[0] for r in refs} == {"A", "B"}


def test_method_with_keyword_arg():
    expr = parse_expr("df['A'].replace(to_replace=df['B'], value=df['C'])")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is not None
    assert len(refs) == 3
    assert {r.col_names[0] for r in refs} == {"A", "B", "C"}


def test_method_no_column_args():
    expr = parse_expr("df['A'].fillna(0)")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is not None
    assert len(refs) == 1
    assert refs[0].col_names == ["A"]


def test_not_a_method_call():
    expr = parse_expr("df['A']")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is None


def test_method_on_non_column():
    expr = parse_expr("some_list.append(df['A'])")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is None


def test_df_names_preserved():
    expr = parse_expr("df1['A'].fillna(df2['B'])")
    refs = extract_column_refs_from_method(expr)
    
    assert refs is not None
    df_names = {r.df_name for r in refs}
    assert df_names == {"df1", "df2"}
```

### Step 4: Add integration tests

```python
# tests/test_method_integration.py
from frame_check_core.checker import Checker


def test_fillna_with_valid_column():
    code = """
import pandas as pd
df = pd.DataFrame({"A": [1, None], "B": [2, 3]})
df["C"] = df["A"].fillna(df["B"])
"""
    fc = Checker.check(code)
    assert len(fc.diagnostics) == 0
    assert "C" in fc.dfs["df"].columns


def test_fillna_with_invalid_column():
    code = """
import pandas as pd
df = pd.DataFrame({"A": [1, None], "B": [2, 3]})
df["C"] = df["A"].fillna(df["X"])  # X doesn't exist
"""
    fc = Checker.check(code)
    assert len(fc.diagnostics) == 1
    assert "X" in fc.diagnostics[0].message
```

### Step 5: Run tests

```sh
cd frame-check-core
uv run pytest tests/test_extractor_method.py tests/test_method_integration.py -v
```


## Type Guards

The `refs.py` module provides type guards for cleaner code:

```python
from frame_check_core.refs import is_name, is_constant, is_subscript, is_binop

# Instead of:
if isinstance(node, ast.Name):
    ...

# Use:
if is_name(node):
    # node is now narrowed to ast.Name
    print(node.id)  # Type checker knows this is valid
```

## Tips

1. **Return `None` early**: If the pattern doesn't match, return `None` immediately so other extractors can try.

2. **Reuse `extract_column_ref`**: This is your building block for recognizing `df['col']` patterns within larger expressions.

3. **Order matters**: In `extract_value_refs`, more specific patterns should come before general ones. Single column refs are checked first as they're most common.

4. **Handle partial matches carefully**: Decide whether partial matches (e.g., `df['A'] + 1`) should return partial results or `None`.

5. **Test edge cases**: Empty lists, nested patterns, mixed DataFrames, etc.

6. **Keep extractors focused**: Each extractor should handle one pattern type. Compose them in `extract_value_refs`.

## Debugging Tips

Use `ast.dump()` to understand node structure:

```python
import ast

code = "df['A'].fillna(df['B'])"
tree = ast.parse(code, mode="eval")
print(ast.dump(tree, indent=2))
```

Output:
```
Expression(
  body=Call(
    func=Attribute(
      value=Subscript(
        value=Name(id='df', ctx=Load()),
        slice=Constant(value='A'),
        ctx=Load()),
      attr='fillna',
      ctx=Load()),
    args=[
      Subscript(
        value=Name(id='df', ctx=Load()),
        slice=Constant(value='B'),
        ctx=Load())],
    keywords=[]))
```

This helps you understand exactly what AST pattern you need to match!
