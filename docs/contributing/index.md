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

5. **Add tests** for your new feature (see [Test Structure](#test-structure) below)

6. **Submit a PR** 🎉

## Test Structure

Tests are organized to mirror the source structure:

```
frame-check-core/tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_checker.py          # Core checker tests
├── config/                  # Tests for config module
│   ├── test_config.py
│   └── test_paths.py
├── diagnostic/              # Tests for diagnostic module
│   ├── test_diagnostics.py
│   └── test_output.py
├── extractors/              # Tests for extractors module
│   ├── test_binop.py
│   ├── test_column.py
│   └── test_registry.py
├── features/                # Feature/API completeness tests
│   ├── test_column_assignment_methods.py  # CAM-* features
│   └── test_dataframe_creation_methods.py # DCMS-* features
└── util/                    # Tests for utility module
    └── test_similarity.py
```

### Where to Add Tests

| Test Type | Location | Example |
|-----------|----------|---------|
| Core checker functionality | `tests/test_checker.py` | Import detection, DataFrame tracking |
| Extractor unit tests | `tests/extractors/test_*.py` | AST pattern matching |
| Config tests | `tests/config/test_*.py` | Config loading, path handling |
| Diagnostic tests | `tests/diagnostic/test_*.py` | Error messages, formatting |
| Feature completeness | `tests/features/test_*.py` | Tests with `@pytest.mark.support` |

### Feature Tests

Tests in `tests/features/` track API completeness and are organized by categories from `scripts/features.toml`:

- `test_dataframe_creation_methods.py` - DCMS-* (DataFrame creation)
- `test_column_assignment_methods.py` - CAM-* (column assignment)

Use the `@pytest.mark.support(code="#DCMS-1")` marker to link tests to features.

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
