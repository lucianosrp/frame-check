# Development Guide - Frame Check VS Code Extension

This guide covers how to develop, test, and contribute to the Frame Check VS Code extension.

## Prerequisites

Before you start developing, make sure you have:

1. **Node.js** (version 16 or higher)
2. **npm** (comes with Node.js)
3. **Visual Studio Code**
4. **frame-check-lsp** installed and accessible in your PATH

### Installing frame-check-lsp

```bash
# From the project root
cd frame-check-lsp
uv tool install . -e
```

Verify installation:
```bash
frame-check-lsp --version
```

## Development Setup

1. **Clone and navigate to the extension directory:**
   ```bash
   cd frame-check-extensions/vscode
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Compile the TypeScript code:**
   ```bash
   npm run compile
   ```

## Development Workflow

### Running the Extension

1. Open the `frame-check-extensions/vscode` directory in VS Code
2. Press `F5` or go to Run > Start Debugging
3. This will:
   - Compile the TypeScript code
   - Launch a new VS Code window (Extension Development Host)
   - Load your extension in the new window

### Testing the Extension

1. In the Extension Development Host window, create a new Python file
2. Write some DataFrame code to test:
   ```python
   import pandas as pd
   
   df = pd.DataFrame({'name': ['Alice'], 'age': [25]})
   print(df['salary'])  # This should show an error
   ```
3. You should see error squiggles and diagnostics

### Making Changes

1. Edit the TypeScript files in `src/`
2. Run `npm run compile` to rebuild
3. Reload the Extension Development Host window (`Ctrl+R` or `Cmd+R`)
4. Test your changes

### Watch Mode

For continuous development, use watch mode:
```bash
npm run watch
```

This automatically recompiles when you save TypeScript files.

## Project Structure

```
vscode/
├── src/
│   └── extension.ts          # Main extension code
├── out/                      # Compiled JavaScript (generated)
├── .vscode/
│   ├── launch.json          # Debug configuration
│   └── tasks.json           # Build tasks
├── package.json             # Extension manifest
├── tsconfig.json           # TypeScript configuration
└── README.md               # Extension documentation
```

### Key Files

- **`src/extension.ts`**: Main extension entry point
  - Handles activation/deactivation
  - Configures the language client
  - Manages the connection to frame-check-lsp

- **`package.json`**: Extension manifest
  - Defines extension metadata
  - Specifies activation events
  - Declares configuration options
  - Lists commands and contributions

## Architecture

The extension follows VS Code's language client architecture:

```
VS Code Extension (Client)
    ↓ LSP Communication
frame-check-lsp (Server)
    ↓ Analysis
frame-check-core (Analysis Engine)
```

### Language Client Setup

The extension uses the `vscode-languageclient` package to communicate with the LSP server:

1. **Server Options**: Specifies how to start the language server
2. **Client Options**: Defines which files to analyze and how to handle communication
3. **Language Client**: Manages the LSP connection and message passing

## Configuration

The extension supports these configuration options:

- `frameCheck.enable`: Enable/disable the extension
- `frameCheck.serverPath`: Path to frame-check-lsp executable
- `frameCheck.trace.server`: Debug tracing level

Add new configuration options in `package.json` under `contributes.configuration.properties`.

## Commands

Current commands:
- `frameCheck.restart`: Restart the language server

Add new commands in `package.json` under `contributes.commands` and implement them in `extension.ts`.

## Debugging

### Extension Debug Output

1. In the Extension Development Host, open Output panel
2. Select "Frame Check Language Server" from the dropdown
3. View server communication and errors

### Trace Communication

Enable tracing in settings:
```json
{
    "frameCheck.trace.server": "verbose"
}
```

### Common Issues

1. **Server not starting**:
   - Check if `frame-check-lsp` is in PATH
   - Look at the output panel for error messages
   - Verify the server path configuration

2. **No diagnostics appearing**:
   - Ensure you're working with `.py` files
   - Check that the extension is activated
   - Verify the language server is running

3. **Compilation errors**:
   - Run `npm run compile` and fix TypeScript errors
   - Check `tsconfig.json` configuration

## Testing

### Manual Testing

1. Create test Python files with DataFrame operations
2. Verify error detection and reporting
3. Test configuration changes
4. Test the restart command

### Test Cases to Cover

- ✅ Basic DataFrame column access errors
- ✅ Multiple DataFrames in one file
- ✅ Complex DataFrame operations
- ✅ Configuration changes
- ✅ Server restart functionality
- ✅ Error message formatting

## Building for Distribution

### Local Build

```bash
npm run vscode:prepublish
```

### Package Extension

```bash
# Install vsce if not already installed
npm install -g vsce

# Package the extension
vsce package
```

This creates a `.vsix` file that can be installed locally:
```bash
code --install-extension frame-check-0.1.0.vsix
```

### Using the Build Script

```bash
./build.sh
```

## Publishing

### Prepare for Publishing

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Ensure all features are tested
4. Update documentation

### Publish to Marketplace

```bash
# Login to Visual Studio Marketplace
vsce login <publisher-name>

# Publish the extension
vsce publish
```

## Contributing

### Code Style

- Use TypeScript strict mode
- Follow VS Code extension conventions
- Add JSDoc comments for public APIs
- Use meaningful variable and function names

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Update documentation
6. Submit a pull request

### Commit Message Format

```
feat: add new configuration option for server timeout
fix: resolve issue with server restart command
docs: update development guide with new testing steps
```

## Troubleshooting Development Issues

### TypeScript Compilation Errors

```bash
# Clean and rebuild
rm -rf out/
npm run compile
```

### VS Code Not Loading Extension

1. Check the Extension Development Host console for errors
2. Verify `package.json` syntax
3. Ensure main entry point exists in `out/extension.js`

### Language Server Connection Issues

1. Test the server manually:
   ```bash
   frame-check-lsp
   ```
2. Check server logs in VS Code output panel
3. Verify server path configuration

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [VS Code Language Client](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide)
- [Extension Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)

## Support

If you encounter issues during development:

1. Check this guide first
2. Look at the existing issues in the repository
3. Create a new issue with detailed information about your problem
4. Include logs from the Extension Development Host and output panels