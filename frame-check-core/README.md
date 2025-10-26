# Frame Check Core

The core static analysis engine for frame-check that tracks pandas DataFrame schemas through Python AST.

## Architecture

### Core Classes

- **`FrameChecker`**: Main AST visitor that tracks DataFrame definitions and column accesses
- **`FrameInstance`**: Represents a DataFrame with its columns and metadata
- **`FrameHistory`**: Tracks DataFrame definitions across different lines for proper scoping
- **`ColumnAccess`**: Represents an attempt to access a column with context information
- **`WrappedNode`**: Type-safe wrapper for AST nodes with convenient attribute access

### WrappedNode Deep Dive

The `WrappedNode` class is a crucial component that provides type-safe, chainable access to AST node attributes. It solves a common problem when working with Python's AST: safely accessing nested attributes without risking `AttributeError` exceptions.

#### Key Features

**Safe Attribute Access**: Instead of manually checking if attributes exist, `WrappedNode` returns empty nodes for missing attributes, allowing for safe method chaining:

```python
# Without WrappedNode - brittle and verbose
if hasattr(node, 'value') and hasattr(node.value, 'func') and hasattr(node.value.func, 'id'):
    func_name = node.value.func.id
else:
    func_name = None

# With WrappedNode - clean and safe
func_name = WrappedNode(node).get("value").get("func").get("id").val
```

**Type Safety**: The class uses generic types and method overloads to provide proper type hints, making the code more maintainable and catching errors at development time.

**Consistent Interface**: All AST node interactions go through the same `.get()` method, providing a uniform API regardless of the underlying node type.

#### Why Use WrappedNode?

1. **Eliminates Boilerplate**: Reduces the need for repeated `hasattr()` checks and defensive programming
2. **Prevents Runtime Crashes**: Gracefully handles missing attributes without throwing exceptions
3. **Improves Readability**: Method chaining makes the intent clear and code more concise
4. **Better Developer Experience**: Type hints provide autocomplete and catch errors early
5. **Consistent Error Handling**: All attribute access failures result in `None` values, making error handling predictable


## Important Notes for Static Analysis

1. **Dynamic column names**: `df[variable] = value` where `variable` contains the column name
2. **Computed column names**: `df[f'col_{i}'] = value` with f-strings or format
3. **Dictionary expansion**: `df = df.assign(**{f'col_{i}': i for i in range(5)})`
4. **Method chaining**: Operations that return new DataFrames vs in-place modifications
5. **Index as columns**: Operations like `reset_index()` can promote index to columns
6. **Conditional existence**: Columns might exist only in certain code paths
7. **External data**: `pd.read_csv()`, `pd.read_excel()` etc. introduce columns from files
8. **SQL queries**: `pd.read_sql()` columns depend on query
9. **Copy vs view**: Some operations create views that share column structure
