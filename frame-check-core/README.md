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

---

# Pandas DataFrame Column Assignment and Removal Methods

## Column Assignment Methods

| ID | Method | Syntax | Example | Notes |
|----|--------|--------|---------|-------|
| <a id="CAM-1"></a>#CAM-1 | **Direct assignment** | `df['col'] = value` | `df['new_col'] = 0` | Most common method |
| <a id="CAM-2"></a>#CAM-2 | **Attribute assignment** | `df.col = value` | `df.new_col = [1,2,3]` | Only works for valid Python identifiers |
| <a id="CAM-3"></a>#CAM-3 | **loc indexer** | `df.loc[:, 'col'] = value` | `df.loc[:, 'A'] = 100` | Can assign to slices |
| <a id="CAM-4"></a>#CAM-4 | **iloc indexer** | `df.iloc[:, index] = value` | `df.iloc[:, 0] = 99` | Position-based assignment |
| <a id="CAM-5"></a>#CAM-5 | **at indexer** | `df.at[row, 'col'] = value` | `df.at[0, 'A'] = 5` | Single cell assignment |
| <a id="CAM-6"></a>#CAM-6 | **iat indexer** | `df.iat[row, col_idx] = value` | `df.iat[0, 1] = 10` | Single cell by position |
| <a id="CAM-7"></a>#CAM-7 | **assign method** | `df = df.assign(col=value)` | `df = df.assign(new=lambda x: x['A']*2)` | Returns new DataFrame |
| <a id="CAM-8"></a>#CAM-8 | **Multiple assign** | `df = df.assign(**kwargs)` | `df = df.assign(B=1, C=2)` | Multiple columns at once |
| <a id="CAM-9"></a>#CAM-9 | **insert method** | `df.insert(loc, 'col', value)` | `df.insert(1, 'new', 0)` | Specify position |
| <a id="CAM-10"></a>#CAM-10 | **setitem with list** | `df[['A','B']] = values` | `df[['X','Y']] = df[['A','B']]` | Multiple columns |
| <a id="CAM-11"></a>#CAM-11 | **From dictionary** | `df = pd.DataFrame(dict)` | `df = pd.DataFrame({'A': [1,2], 'B': [3,4]})` | Constructor |
| <a id="CAM-12"></a>#CAM-12 | **concat** | `df = pd.concat([df, new_df], axis=1)` | `df = pd.concat([df, df2], axis=1)` | Horizontal concatenation |
| <a id="CAM-13"></a>#CAM-13 | **join** | `df = df.join(other_df)` | `df = df.join(df2[['C']])` | Adds columns from other DataFrame |
| <a id="CAM-14"></a>#CAM-14 | **merge** | `df = df.merge(df2)` | `df = df.merge(df2, on='key')` | Can add columns via merge |
| <a id="CAM-15"></a>#CAM-15 | **From eval** | `df.eval('new = A + B')` | `df.eval('C = A * 2', inplace=True)` | String expression assignment |
| <a id="CAM-16"></a>#CAM-16 | **From query results** | `df['new'] = df.query('A > 0')['B']` | Various query-based assignments | Indirect assignment |
| <a id="CAM-17"></a>#CAM-17 | **Conditional assignment** | `df.loc[condition, 'col'] = value` | `df.loc[df['A'] > 0, 'B'] = 1` | Partial column updates |
| <a id="CAM-18"></a>#CAM-18 | **Copy from another column** | `df['new'] = df['existing'].copy()` | `df['B'] = df['A'].copy()` | Explicit copy |
| <a id="CAM-19"></a>#CAM-19 | **Transform operations** | `df['new'] = df['col'].apply(func)` | `df['B'] = df['A'].apply(lambda x: x*2)` | Via transformations |
| <a id="CAM-20"></a>#CAM-20 | **Expanding columns** | `df[['A','B']] = df['combined'].str.split(expand=True)` | String split to multiple cols | Creates multiple columns |
| <a id="CAM-21"></a>#CAM-21 | **From groupby** | `df['new'] = df.groupby('A')['B'].transform('mean')` | Groupby aggregations | Broadcast results back |
| <a id="CAM-22"></a>#CAM-22 | **From pivot** | Pivot operations can create new columns | `df.pivot(columns='A')` | Reshaping creates columns |
| <a id="CAM-23"></a>#CAM-23 | **From unstack** | `df = df.unstack()` | Multi-index to columns | Index level to columns |
| <a id="CAM-24"></a>#CAM-24 | **From pd.get_dummies** | `df = pd.get_dummies(df, columns=['A'])` | One-hot encoding | Creates multiple columns |
| <a id="CAM-25"></a>#CAM-25 | **Update method** | `df.update(other_df)` | `df.update(df2[['A']])` | Updates existing columns |

## Column Removal Methods

| ID | Method | Syntax | Example | Notes |
|----|--------|--------|---------|-------|
| <a id="CRM-1"></a>#CRM-1 | **del statement** | `del df['col']` | `del df['A']` | In-place removal |
| <a id="CRM-2"></a>#CRM-2 | **drop method** | `df = df.drop('col', axis=1)` | `df = df.drop('A', axis=1)` | Returns new DataFrame |
| <a id="CRM-3"></a>#CRM-3 | **drop with columns** | `df = df.drop(columns=['col'])` | `df = df.drop(columns=['A', 'B'])` | More explicit |
| <a id="CRM-4"></a>#CRM-4 | **drop multiple** | `df = df.drop(['A','B'], axis=1)` | List of columns | Multiple at once |
| <a id="CRM-5"></a>#CRM-5 | **pop method** | `series = df.pop('col')` | `removed = df.pop('A')` | Removes and returns |
| <a id="CRM-6"></a>#CRM-6 | **Assign None** | `df = df.assign(col=None)` | Not common | Indirect removal |
| <a id="CRM-7"></a>#CRM-7 | **Select subset** | `df = df[['A', 'B']]` | `df = df[keep_cols]` | Keep only specified |
| <a id="CRM-8"></a>#CRM-8 | **loc selection** | `df = df.loc[:, ['A', 'B']]` | Keep only selected | Indirect removal |
| <a id="CRM-9"></a>#CRM-9 | **iloc selection** | `df = df.iloc[:, [0, 1]]` | Position-based selection | Indirect removal |
| <a id="CRM-10"></a>#CRM-10 | **Boolean mask** | `df = df.loc[:, mask]` | `df = df.loc[:, ~df.columns.str.startswith('temp')]` | Conditional removal |
| <a id="CRM-11"></a>#CRM-11 | **filter method** | `df = df.filter(items=['A'])` | `df = df.filter(regex='^[AB]')` | Pattern-based selection |
| <a id="CRM-12"></a>#CRM-12 | **drop_duplicates** | Can remove columns implicitly | If transposed | Edge case |
| <a id="CRM-13"></a>#CRM-13 | **Reindex** | `df = df.reindex(columns=['A','B'])` | Specify kept columns | Indirect removal |

## Edge Cases and Special Considerations

| ID | Scenario | Example | Impact on Columns |
|----|----------|---------|-------------------|
| <a id="EC-1"></a>#EC-1 | **MultiIndex columns** | `df.columns = pd.MultiIndex.from_tuples(...)` | Complex column structure |
| <a id="EC-2"></a>#EC-2 | **Rename operations** | `df = df.rename(columns={'old': 'new'})` | Changes column names |
| <a id="EC-3"></a>#EC-3 | **Set operations** | `df.columns = ['A', 'B', 'C']` | Complete replacement |
| <a id="EC-4"></a>#EC-4 | **Arithmetic operations** | `df['C'] = df['A'] + df['B']` | Creates new columns |
| <a id="EC-5"></a>#EC-5 | **String accessor** | `df[['first', 'last']] = df['name'].str.split(expand=True)` | Expands to multiple |
| <a id="EC-6"></a>#EC-6 | **JSON normalization** | `pd.json_normalize()` | Creates nested column names |
| <a id="EC-7"></a>#EC-7 | **Pivot operations** | `df.pivot_table()` | Reshapes column structure |
| <a id="EC-8"></a>#EC-8 | **Stack/unstack** | `df.stack()` / `df.unstack()` | Converts between index/columns |
| <a id="EC-9"></a>#EC-9 | **Transpose** | `df.T` | Swaps rows and columns |
| <a id="EC-10"></a>#EC-10 | **Column assignment in chain** | `df.assign(B=1).assign(C=lambda x: x['B']*2)` | Chained assignments |

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



#### DataFrame Creation Support Matrix

The following table shows various ways to create pandas DataFrames and their current support status in frame-check:

| ID | Creation Method | Example | Supported | Notes |
|----|-----------------|---------|-----------|-------|
| <a id="DCMS-1"></a>#DCMS-1 | **Dictionary of Lists** | `pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})` | ✅ | Fully supported - primary use case |
| <a id="DCMS-2"></a>#DCMS-2 | **List of Dictionaries** | `pd.DataFrame([{'col1': 1, 'col2': 3}, {'col1': 2, 'col2': 4}])` | ❌ | Not yet implemented |
| <a id="DCMS-3"></a>#DCMS-3 | **Dictionary of Series** | `pd.DataFrame({'col1': pd.Series([1, 2]), 'col2': pd.Series([3, 4])})` | ❌ | Not yet implemented |
| <a id="DCMS-4"></a>#DCMS-4 | **NumPy Array** | `pd.DataFrame(np.array([[1, 2], [3, 4]]), columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| <a id="DCMS-5"></a>#DCMS-5 | **List of Lists** | `pd.DataFrame([[1, 2], [3, 4]], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| <a id="DCMS-6"></a>#DCMS-6 | **From CSV** | `pd.read_csv('file.csv')` | ❌ | Not yet implemented |
| <a id="DCMS-7"></a>#DCMS-7 | **From JSON** | `pd.read_json('file.json')` | ❌ | Not yet implemented |
| <a id="DCMS-8"></a>#DCMS-8 | **From SQL** | `pd.read_sql('SELECT * FROM table', connection)` | ❌ | Not yet implemented |
| <a id="DCMS-9"></a>#DCMS-9 | **From Excel** | `pd.read_excel('file.xlsx')` | ❌ | Not yet implemented |
| <a id="DCMS-10"></a>#DCMS-10 | **From Parquet** | `pd.read_parquet('file.parquet')` | ❌ | Not yet implemented |
| <a id="DCMS-11"></a>#DCMS-11 | **Empty DataFrame** | `pd.DataFrame()` | ❌ | Not yet implemented |
| <a id="DCMS-12"></a>#DCMS-12 | **From Index** | `pd.DataFrame(index=['a', 'b'], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| <a id="DCMS-13"></a>#DCMS-13 | **From Scalar** | `pd.DataFrame({'col1': 1}, index=[0, 1, 2])` | ❌ | Not yet implemented |
| <a id="DCMS-14"></a>#DCMS-14 | **Copy Constructor** | `pd.DataFrame(other_df)` | ❌ | Not yet implemented |
| <a id="DCMS-15"></a>#DCMS-15 | **From Records** | `pd.DataFrame.from_records([('a', 1), ('b', 2)], columns=['col1', 'col2'])` | ❌ | Not yet implemented |
| <a id="DCMS-16"></a>#DCMS-16 | **From Dict** | `pd.DataFrame.from_dict({'col1': [1, 2], 'col2': [3, 4]})` | ❌ | Not yet implemented |

**Legend:**
- ✅ Fully supported
- 🟡 Partially supported
- ❌ Not yet implemented


