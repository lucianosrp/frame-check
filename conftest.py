import inspect
import os
import re
from typing import NamedTuple

import pandas as pd
import pytest


# Store test results
class SupportResult(NamedTuple):
    feature_code: str
    name: str
    example: str
    supported: bool


_support_results: list[SupportResult] = []


def pytest_addoption(parser):
    """Add --support command line option."""
    parser.addoption(
        "--support",
        action="store_true",
        default=False,
        help="Generate feature support documentation",
    )


def pytest_configure(config):
    """Register the support marker."""
    config.addinivalue_line(
        "markers", "support(name): mark test to track feature support status"
    )


def extract_example_from_test(item):
    """Extract the code example from test function, skipping first two lines."""
    try:
        # Get the test function source code
        source = inspect.getsource(item.function)

        # Find the `code = """` block
        lines = source.split("\n")

        # Find start of triple-quoted string
        start_idx = None
        for i, line in enumerate(lines):
            if 'code = """' in line or "code = '''" in line:
                start_idx = i + 1  # Start after the opening line
                break

        if start_idx is None:
            return "N/A"

        # Find end of triple-quoted string
        end_idx = None
        for i in range(start_idx, len(lines)):
            if '"""' in lines[i] or "'''" in lines[i]:
                end_idx = i
                break

        if end_idx is None:
            return "N/A"

        # Extract the code lines
        code_lines = lines[start_idx:end_idx]

        # Skip first two lines (import pandas and DataFrame creation)
        if len(code_lines) > 2:
            example_lines = code_lines[2:]
            # Remove leading whitespace and join
            example = "\n".join(line.strip() for line in example_lines if line.strip())
            return example

        return "N/A"

    except Exception:
        return "N/A"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for tests marked with @support."""
    outcome = yield
    report = outcome.get_result()

    # Only collect if --support flag is enabled
    if not item.config.getoption("--support"):
        return

    # Only process the 'call' phase (actual test execution, not setup/teardown)
    if report.when == "call":
        # Check if test has the support marker
        support_marker = item.get_closest_marker("support")
        if support_marker:
            # Get the feature name from the marker
            feature_name = support_marker.kwargs.get("name", item.name)

            feature_code = support_marker.kwargs.get("code", "")

            # Try to get example from marker, otherwise extract from code
            feature_example = support_marker.kwargs.get(
                "example", extract_example_from_test(item)
            )

            # Store whether the test passed
            _support_results.append(
                SupportResult(
                    feature_code,
                    feature_name,
                    feature_example,
                    report.outcome == "passed",
                )
            )


def update_readme(df: pd.DataFrame):
    """
    Update readme support table
    Update section under ## Supported Features header
    """
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print(f"Warning: {readme_path} not found, skipping update.")
        return

    # Read the README content
    with open(readme_path, "r") as f:
        content = f.read()

    # Find the supported features section
    support_section_pattern = r"## Supported Features\s*\n(.*?)\n---"
    match = re.search(support_section_pattern, content, re.DOTALL)
    if not match:
        print("Warning: Could not find '## Supported Features' section in README.md")
        return

    # Format the table
    df["feature_code"] = '<a id="' + df["feature_code"] + '"></a>' + df["feature_code"]
    table = df.replace({True: "✅", False: "❌"}).to_markdown(index=False)

    # Replace the section with new content
    new_section = f"## Supported Features\n\n{table}\n\nNote: some not-supported features may not be present in this list\n\n---"
    new_content = re.sub(support_section_pattern, new_section, content, flags=re.DOTALL)

    # Write back to README
    with open(readme_path, "w") as f:
        f.write(new_content)

    print(f"Updated support table in {readme_path}")


def pytest_sessionfinish(session, exitstatus):
    """Write support results to a file after all tests complete."""
    # Only write report if --support flag is enabled
    if not session.config.getoption("--support"):
        return

    if not _support_results:
        print("\nNo @support marked tests found.")
        return

    import pandas as pd

    df = pd.DataFrame(_support_results).sort_values(
        ["feature_code", "name", "example"]  # Sort for consistency
    )

    print()
    print("\n" + "=" * 24)
    print("Feature Support Summary:")
    print()
    print(df.to_markdown(index=False, tablefmt="rounded_grid"))
    print()

    # Update the README.md file with support information
    update_readme(df)
