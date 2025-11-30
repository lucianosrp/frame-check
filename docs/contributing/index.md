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
│   ├── column.py       # df['col'] patterns
│   └── binop.py        # df['A'] + df['B'] patterns
├── diagnostic/         # Error message generation
└── config/             # Configuration management
```

## Extension Points

frame-check is designed to be extensible. There are three main ways to add features:

| Extension Type | Use Case | Difficulty |
|---------------|----------|------------|
| [Pandas Function](./adding-pandas-function.md) | Add support for `pd.read_excel()`, `pd.concat()`, etc. | ⭐ Easy |
| [DataFrame Method](./adding-dataframe-method.md) | Add support for `df.drop()`, `df.rename()`, etc. | ⭐ Easy |
| [Extractor](./adding-extractor.md) | Handle new column reference patterns | ⭐⭐ Easy-Medium |

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
- **Test thoroughly**: Each feature should have corresponding tests
- **Document clearly**: Add docstrings and update relevant documentation