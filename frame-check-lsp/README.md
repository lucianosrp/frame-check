# Frame Check LSP

A Language Server Protocol (LSP) implementation for frame-check.

## Features

- **Real-time error detection**: Identifies when you're trying to access columns that don't exist in your DataFrame
- **Detailed error messages**: Shows exactly where the DataFrame was defined and what columns are available
- **Editor integration**: Works with any LSP-compatible editor (VS Code, Neovim, Emacs, etc.)

## Installation

### Development Installation

To install for development:

```bash
uv tool install . -e
```

This will install the package in editable mode, allowing you to make changes to the code and see them reflected immediately.
