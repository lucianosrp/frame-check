# Frame Check Core

The core static analysis engine for frame-check that tracks pandas DataFrame schemas through Python AST.
`
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


#### Pandas Column Operations Support Matrix

The following table shows various ways to create and assign columns in pandas DataFrames and their current support status in frame-check:

| Operation | Example | Supported | Notes |
|-----------|---------|-----------|-------|
| **Direct Assignment** | `df['new_col'] = values` | 🟡 | Needs testing |
| **Multiple Assignment** | `df[['col1', 'col2']] = values` | ❌ | Not yet implemented |
| **Conditional Assignment** | `df.loc[condition, 'col'] = value` | ❌ | Not yet implemented |
| **Index-based Assignment** | `df.iloc[:, 0] = values` | ❌ | Not yet implemented |
| **assign() Method** | `df.assign(new_col=lambda x: x['old_col'] * 2)` | ✅ | Supported with lambda tracking |
| **insert() Method** | `df.insert(0, 'new_col', values)` | ❌ | Not yet implemented |
| **eval() Method** | `df.eval('new_col = col1 + col2')` | ❌ | Not yet implemented |
| **query() Method** | `df.query('col > 5')` | ❌ | Not yet implemented - doesn't create columns |
| **with_columns() Method** | `df.with_columns(new_col=expr)` | ❌ | Polars-style, not applicable to pandas |
| **Groupby Aggregation** | `df.groupby('col')['other'].sum()` | ❌ | Not yet implemented |
| **Transform Operations** | `df.transform({'col': func})` | ❌ | Not yet implemented |
| **Map/Apply Results** | `df['new'] = df['old'].apply(func)` | ❌ | Not yet implemented |

**Legend:**
- ✅ Fully supported
- 🟡 Partially supported
- ❌ Not yet implemented


####DataFrame Creation Support Matrix

The following table shows various ways to create pandas DataFrames and their current support status in frame-check:

| Creation Method | Example | Supported | Notes |
|-----------------|---------|-----------|-------|
| **Dictionary of Lists** | `pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})` | ✅ | Fully supported - primary use case |
| **List of Dictionaries** | `pd.DataFrame([{'col1': 1, 'col2': 3}, {'col1': 2, 'col2': 4}])` | ❌ | Not yet implemented |
| **Dictionary of Series** | `pd.DataFrame({'col1': pd.Series([1, 2]), 'col2': pd.Series([3, 4])})` | ❌ | Not yet implemented |
| **NumPy Array** | `pd.DataFrame(np.array([[1, 2], [3, 4]]), columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| **List of Lists** | `pd.DataFrame([[1, 2], [3, 4]], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| **From CSV** | `pd.read_csv('file.csv')` | ❌ | Not yet implemented |
| **From JSON** | `pd.read_json('file.json')` | ❌ | Not yet implemented |
| **From SQL** | `pd.read_sql('SELECT * FROM table', connection)` | ❌ | Not yet implemented |
| **From Excel** | `pd.read_excel('file.xlsx')` | ❌ | Not yet implemented |
| **From Parquet** | `pd.read_parquet('file.parquet')` | ❌ | Not yet implemented |
| **Empty DataFrame** | `pd.DataFrame()` | ❌ | Not yet implemented |
| **From Index** | `pd.DataFrame(index=['a', 'b'], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| **From Scalar** | `pd.DataFrame({'col1': 1}, index=[0, 1, 2])` | ❌ | Not yet implemented |
| **Copy Constructor** | `pd.DataFrame(other_df)` | ❌ | Not yet implemented |
| **From Records** | `pd.DataFrame.from_records([('a', 1), ('b', 2)], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| **From Dict** | `pd.DataFrame.from_dict({'col1': [1, 2], 'col2': [3, 4]})` | ❌ | Not yet implemented |

**Legend:**
- ✅ Fully supported
- 🟡 Partially supported
- ❌ Not yet implemented
