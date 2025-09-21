# Sprint Guidelines for frame-check

Welcome to the frame-check sprint! This project aims to bring static type checking to pandas DataFrames, catching column access errors before runtime.

## 🎯 Sprint Goals

- Expand DataFrame creation support beyond dictionary-of-lists
- Add support for more column assignment patterns
- Improve error messages and diagnostics
- Enhance editor integration
- Add comprehensive test coverage

## 🚀 How to Contribute

### Getting Started

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/frame-check.git
   cd frame-check
   ```

2. **Set up Development Environment**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync
   ```

3. **Test the Current Implementation**
   ```bash
   # Test the core functionality
   uv run frame-check-core example.py

   # Test the LSP server
   uv run frame-check-lsp
   ```

### 📋 Current Sprint Tasks

#### High Priority (Good First Issues)

1. **Expand DataFrame Creation Support**
   - [ ] List of dictionaries: `pd.DataFrame([{'col1': 1, 'col2': 2}])`
   - [ ] List of lists with columns: `pd.DataFrame([[1, 2]], columns=['col1', 'col2'])`
   - [ ] Empty DataFrame with columns: `pd.DataFrame(columns=['col1', 'col2'])`

2. **Column Assignment Patterns**
   - [ ] Multiple column assignment: `df[['col1', 'col2']] = values`
   - [ ] Conditional assignment: `df.loc[condition, 'col'] = value`
   - [ ] Insert method: `df.insert(0, 'new_col', values)`

3. **Improve Error Messages**
   - [ ] Add "did you mean" suggestions for typos
   - [ ] Show available columns in error messages
   - [ ] Add line-specific column highlighting

#### Medium Priority

4. **Data Reading Functions**
   - [ ] `pd.read_csv()` - could use header inference or explicit columns
   - [ ] `pd.read_json()` - basic structure detection
   - [ ] Basic file format support

5. **DataFrame Operations**
   - [ ] `df.assign()` improvements - handle complex lambda expressions
   - [ ] `df.groupby()` result column tracking
   - [ ] `df.merge()` and `df.join()` column combination

6. **Testing Infrastructure**
   - [ ] Add pytest test suite
   - [ ] Create test cases for all supported patterns
   - [ ] Add regression tests for error cases

#### Advanced Tasks

7. **LSP Enhancements**
   - [ ] Real-time column completion
   - [ ] Hover information for DataFrames
   - [ ] Code actions for common fixes

8. **Editor Extensions**
   - [ ] VS Code extension
   - [ ] Neovim plugin improvements
   - [ ] JetBrains IDE support

## 🛠️ Development Workflow

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Focus on one feature at a time
   - Update the support matrices in README files
   - Add test cases for new functionality

3. **Test Your Changes**
   ```bash
   # Test core functionality
   uv run frame-check-core example.py

   # Test with your own examples
   echo "import pandas as pd
   df = pd.DataFrame([{'name': 'Alice', 'age': 25}])
   print(df['nonexistent'])" > test.py
   uv run frame-check-core test.py
   ```

4. **Submit a Pull Request**
   - Describe what your change does
   - Reference any related issues
   - Include before/after examples if applicable

### 📝 Code Style

- Follow existing code patterns
- Use type hints where possible
- Add docstrings to new functions
- Keep functions focused and small

### 🧪 Testing Your Work

Create test files to verify your changes work correctly:

```python
# test_new_feature.py
import pandas as pd

# Test case 1: Your new feature
df = pd.DataFrame([{'col1': 1, 'col2': 2}])  # Your new support
result = df['col1']  # Should work
error = df['col3']   # Should trigger error

# Test case 2: Edge cases
empty_df = pd.DataFrame()
# ... add more test cases
```

Run with: `uv run frame-check-core test_new_feature.py`

## 🐛 Found a Bug?

1. Check if it's already reported in issues
2. Create a minimal reproduction case
3. Submit an issue with:
   - The code that doesn't work
   - Expected vs actual behavior
   - Your environment details

## 💡 Ideas and Suggestions

Have an idea for improvement?

1. Check existing issues and discussions
2. Open a discussion or issue to talk about it
3. Consider if it fits the current sprint goals
4. Start working on it if it's greenlit!

## 🤝 Getting Help

- **Stuck on implementation?** Open a discussion or comment on the issue
- **Not sure where to start?** Look for issues tagged with "good first issue"
- **Want to pair program?** Reach out to other contributors

## 📊 Current Status

Track our progress in the support matrices:
- **DataFrame Creation**: 1/10+ patterns supported
- **Column Assignment**: 1/8+ patterns supported
- **Data Reading**: 0/6+ functions supported

Let's build something amazing together! 🐼✨
