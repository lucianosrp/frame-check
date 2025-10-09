# Frame Check VS Code Extension

A VS Code extension that provides real-time DataFrame column validation for Python code using the Frame Check Language Server Protocol (LSP).

## Features

- **Real-time error detection**: Identifies when you're trying to access columns that don't exist in your DataFrame
- **Detailed error messages**: Shows exactly where the DataFrame was defined and what columns are available
- **Seamless integration**: Works automatically with Python files in VS Code
- **Configurable**: Customize the language server path and behavior

## Installation

### Prerequisites

You need to have the `frame-check-lsp` language server installed on your system. Install it using:

```bash
uv tool install frame-check-lsp
```

Or for development:

```bash
cd frame-check-lsp
uv tool install . -e
```

### Extension Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Frame Check"
4. Install the extension

## Usage

The extension automatically activates when you open Python files. It will:

1. Analyze your DataFrame operations
2. Show red squiggly lines under invalid column access attempts
3. Provide hover information about available columns
4. Display error messages in the Problems panel

### Example

```python
import pandas as pd

# Create a DataFrame
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})

# This will show an error - 'salary' column doesn't exist
print(df['salary'])  # ❌ Error: Column 'salary' not found

# This works fine
print(df['name'])    # ✅ OK
```

## Configuration

You can configure the extension through VS Code settings:

- `frameCheck.enable`: Enable/disable the Frame Check language server (default: `true`)
- `frameCheck.serverPath`: Path to the frame-check-lsp executable (default: `"frame-check-lsp"`)
- `frameCheck.trace.server`: Set trace level for debugging (default: `"off"`)

### Setting the Server Path

If the `frame-check-lsp` command is not in your PATH, you can specify the full path:

```json
{
    "frameCheck.serverPath": "/path/to/frame-check-lsp"
}
```

## Commands

- `Frame Check: Restart Language Server` - Restart the Frame Check language server

## Troubleshooting

### Language Server Not Starting

1. Ensure `frame-check-lsp` is installed and accessible:
   ```bash
   frame-check-lsp --version
   ```

2. Check the Output panel (View → Output → Frame Check Language Server) for error messages

3. Try restarting the language server using the command palette:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "Frame Check: Restart Language Server"

### No Error Detection

1. Make sure you're working with a Python file (`.py` extension)
2. Check that the extension is enabled in settings
3. Verify your code uses supported DataFrame operations

## Development

To build and run the extension locally:

```bash
cd frame-check-extensions/vscode
npm install
npm run compile
```

Then press F5 in VS Code to launch a new Extension Development Host window.

## Contributing

Contributions are welcome! Please see the main [Frame Check repository](https://github.com/lucianosrp/frame-check) for contribution guidelines.

## License

MIT License - see the [LICENSE](../../LICENSE.md) file for details.