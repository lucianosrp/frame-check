#!/bin/bash

# Build script for Frame Check VS Code Extension

set -e

echo "🔨 Building Frame Check VS Code Extension..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if vsce is installed, install if not
if ! command -v vsce &> /dev/null; then
    echo "📦 Installing vsce (Visual Studio Code Extension manager)..."
    npm install -g vsce
fi

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Compile TypeScript
echo "🔧 Compiling TypeScript..."
npm run compile

# Run basic checks
echo "✅ Running pre-package checks..."

# Check if main files exist
if [ ! -f "out/extension.js" ]; then
    echo "❌ Compiled extension.js not found. Compilation may have failed."
    exit 1
fi

if [ ! -f "package.json" ]; then
    echo "❌ package.json not found."
    exit 1
fi

# Package the extension
echo "📦 Packaging extension..."
vsce package

# Find the generated .vsix file
VSIX_FILE=$(ls *.vsix 2>/dev/null | head -n 1)

if [ -n "$VSIX_FILE" ]; then
    echo "✅ Extension packaged successfully: $VSIX_FILE"
    echo ""
    echo "To install the extension:"
    echo "  code --install-extension $VSIX_FILE"
    echo ""
    echo "To publish the extension:"
    echo "  vsce publish"
else
    echo "❌ No .vsix file found. Packaging may have failed."
    exit 1
fi

echo "🎉 Build complete!"
