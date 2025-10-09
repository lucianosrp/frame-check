#!/bin/bash

# Installation script for Frame Check VS Code Extension Development Setup
# This script sets up the development environment for the Frame Check VS Code extension

set -e

echo "🚀 Frame Check VS Code Extension Development Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the VS Code extension directory."
    exit 1
fi

# Check Node.js installation
print_status "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    print_error "Node.js version 16 or higher is required. Current version: $(node --version)"
    exit 1
fi

print_success "Node.js $(node --version) is installed"

# Check npm installation
print_status "Checking npm installation..."
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi
print_success "npm $(npm --version) is installed"

# Install dependencies
print_status "Installing npm dependencies..."
if npm install; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Install vsce (VS Code Extension CLI) globally if not present
print_status "Checking Visual Studio Code Extension CLI (vsce)..."
if ! command -v vsce &> /dev/null; then
    print_status "Installing vsce globally..."
    if npm install -g vsce; then
        print_success "vsce installed successfully"
    else
        print_error "Failed to install vsce. You may need to run with sudo or use a Node version manager."
        print_warning "You can install it later with: npm install -g vsce"
    fi
else
    print_success "vsce is already installed"
fi

# Check if frame-check-lsp is installed
print_status "Checking frame-check-lsp installation..."
if command -v frame-check-lsp &> /dev/null; then
    print_success "frame-check-lsp is installed and accessible"
    FRAME_CHECK_VERSION=$(frame-check-lsp --version 2>/dev/null || echo "unknown")
    print_status "Version: $FRAME_CHECK_VERSION"
else
    print_warning "frame-check-lsp is not found in PATH"
    print_status "To install frame-check-lsp, run from the project root:"
    echo "  cd ../../../frame-check-lsp"
    echo "  uv tool install . -e"
    echo ""
fi

# Compile TypeScript
print_status "Compiling TypeScript..."
if npm run compile; then
    print_success "TypeScript compiled successfully"
else
    print_error "TypeScript compilation failed"
    exit 1
fi

# Check if VS Code is installed
print_status "Checking Visual Studio Code installation..."
if command -v code &> /dev/null; then
    print_success "VS Code is installed and accessible from command line"
else
    print_warning "VS Code command 'code' not found in PATH"
    print_status "Make sure VS Code is installed and the 'code' command is available"
    print_status "In VS Code: View > Command Palette > 'Shell Command: Install code command in PATH'"
fi

# Create .vscode/settings.json with recommended settings
print_status "Setting up VS Code workspace settings..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
    "typescript.preferences.includePackageJsonAutoImports": "on",
    "typescript.suggest.autoImports": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "out": false,
        "**/*.vsix": true
    },
    "search.exclude": {
        "out": true,
        "node_modules": true,
        "**/*.vsix": true
    },
    "typescript.tsc.autoDetect": "on"
}
EOF

print_success "Workspace settings configured"

echo ""
print_success "🎉 Development setup completed successfully!"
echo ""
print_status "Next steps:"
echo "1. Open this directory in VS Code:"
echo "   code ."
echo ""
echo "2. Press F5 to launch the Extension Development Host"
echo ""
echo "3. In the new window, open a Python file and test DataFrame operations"
echo ""
echo "4. Make changes to src/extension.ts and reload the extension (Ctrl+R)"
echo ""

if ! command -v frame-check-lsp &> /dev/null; then
    print_warning "Don't forget to install frame-check-lsp for the extension to work!"
fi

print_status "For more information, see DEVELOPMENT.md"
print_status "Happy coding! 🚀"
