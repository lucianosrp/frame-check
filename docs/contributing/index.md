# Contributing to frame-check

Welcome! This section covers how to extend and contribute to frame-check.

## Architecture Overview

The `frame-check-core` package is built around these key components:

```
frame-check-core/
├── checker.py          # Main AST visitor (entry point)
├── tracker.py          # Column dependency tracking
├── refs.py             # Type guards and ColumnRef dataclass
├── ast/
│   ├── models.py       # PD/DF registries for method handlers
│   ├── pandas.py       # pd.* function handlers
│   └── dataframe.py    # df.* method handlers
├── extractors/         # Column reference extraction
│   ├── registry.py     # Extractor registry
│   ├── column.py       # df['col'] patterns
│   └── binop.py        # df['A'] + df['B'] patterns
├── diagnostic/         # Error message generation
└── config/             # Configuration management
```

## Extension Points

frame-check is designed to be extensible using **decorator-based registries**. There are three main ways to add features:

| Extension Type | Decorator | Use Case | Difficulty |
|---------------|-----------|----------|------------|
| [Pandas Function](./adding-pandas-function.md) | `@PD.register()` | Add support for `pd.read_excel()`, `pd.concat()`, etc. | ⭐ Easy |
| [DataFrame Method](./adding-dataframe-method.md) | `@DF.register()` | Add support for `df.drop()`, `df.rename()`, etc. | ⭐ Easy |
| [Extractor](./adding-extractor.md) | `@Extractor.register()` | Handle new column reference patterns | ⭐ Easy |

### Registry Pattern

All three extension types follow the same pattern:

```python
# Pandas functions
@PD.register("read_excel")
def pd_read_excel(args, keywords) -> PDFuncResult:
    ...

# DataFrame methods
@DF.register("drop")
def df_drop(columns, args, keywords) -> DFFuncResult:
    ...

# Extractors
@Extractor.register(priority=40, name="method_call")
def extract_method_call(node: ast.expr) -> list[ColumnRef] | None:
    ...
```

This means:
- **No manual registration** - decorators handle it automatically
- **Automatic discovery** - just import the module
- **Priority ordering** - extractors are tried in priority order
- **Easy testing** - registries can be cleared/modified in tests

## Quick Start

1. **Clone the repository**
   ```sh
   git clone https://github.com/lucianosrp/frame-check.git
   cd frame-check
   ```

2. **Set up development environment**
   ```sh
   cd frame-check-core
   uv sync --group dev
   ```

3. **Run tests**
   ```sh
   uv run pytest
   ```

4. **Make your changes** following the guides above

5. **Add tests** for your new feature

6. **Submit a PR** 🎉

## Design Principles

When contributing, keep these principles in mind:

- **Fail gracefully**: Return `None` when a pattern isn't recognized rather than crashing
- **Be conservative**: Only report errors when you're confident something is wrong
- **Compose existing tools**: Reuse extractors and utilities where possible
- **Use the registries**: Don't hardcode - use `@PD.register()`, `@DF.register()`, or `@Extractor.register()`
- **Test thoroughly**: Each feature should have corresponding tests
- **Document clearly**: Add docstrings and update relevant documentation

## What to Contribute

### High Impact, Easy to Add

- **Pandas functions**: `pd.read_excel`, `pd.read_json`, `pd.read_parquet`, `pd.concat`
- **DataFrame methods**: `df.drop`, `df.rename`, `df.copy`, `df.reset_index`
- **Extractors**: Method calls (`df['A'].fillna(df['B'])`), comparisons (`df['A'] > df['B']`)

### Medium Effort

- Method chaining support (`df.assign(A=1).drop('B')`)
- `from pandas import DataFrame` imports
- Groupby result column inference

### Advanced

- Control flow analysis (if/else branches)
- Function boundary analysis (parameters and returns)
- Polars support
