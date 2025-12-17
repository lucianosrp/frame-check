import os
import re
from typing import NamedTuple

import pandas as pd
import pytest
import tomlkit
from tomlkit.toml_document import TOMLDocument


# Store test results
class SupportResult(NamedTuple):
    feature_code: str
    name: str
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
            feature_name = support_marker.kwargs.get("name")
            feature_code = support_marker.kwargs.get("code", "")

            # Store whether the test passed
            _support_results.append(
                SupportResult(
                    feature_code,
                    feature_name,
                    report.outcome == "passed",
                )
            )


def update_markdown(dataframes: dict[str, pd.DataFrame], markdown_path: str):
    """
    Update markdown support tables
    Update section under ## Supported Features header
    """
    if not os.path.exists(markdown_path):
        print(f"Warning: {markdown_path} not found, skipping update.")
        return

    # Read the markdown content
    with open(markdown_path, "r") as f:
        content = f.read()

    # Build the new section content (tables only)
    new_section = "## Supported Features\n\n"

    # Add each section's table
    for section_name, df in dataframes.items():
        # Add section heading
        new_section += f"### {section_name}\n\n"

        # Format the table
        df["id"] = '<a id="' + df["id"] + '"></a>' + df["id"]
        table = df.replace({True: "✅", False: "❌"}).to_markdown(index=False)
        new_section += f"{table}\n\n"

    # Add README-specific note if applicable (preserves it across updates)
    if "README" in markdown_path:
        new_section += """Note: the full list of supported features can be found [here](https://frame-check.github.io/frame-check/features/).\n\n"""

    # NEW LOGIC: Use slicing to replace only the inner section content, preserving --- and footer
    # Find the start of the header (fixed to ##, multiline search)
    header_pattern = r"##\s*Supported Features"
    match = re.search(header_pattern, content, re.MULTILINE)
    if not match:
        print(
            f"Warning: Could not find '## Supported Features' section in {markdown_path}"
        )
        return

    start = match.start()

    from_start = content[start:]
    dash_match = re.search(r"\n---", from_start)
    if dash_match:
        dash_pos = start + dash_match.start()
        prefix = content[:start]
        new_content = prefix + new_section + content[dash_pos:]
    else:
        print(
            f"Warning: No '---' found after section in {markdown_path}; replacing to end."
        )
        prefix = content[:start]
        new_content = prefix + new_section

    # Write back to markdown
    with open(markdown_path, "w") as f:
        f.write(new_content)


def pytest_sessionfinish(session, exitstatus):
    """Write support results to a file after all tests complete and update features.toml."""
    # Only write report if --support flag is enabled
    if not session.config.getoption("--support"):
        return

    if not _support_results:
        print("\nNo @support marked tests found.")
        return

    doc = update_features_toml(_support_results)
    # Update the markdown files with support information
    # NOTE: Paths may need adjustment based on project structure (e.g., ../../README.md from tests/)
    if doc:
        section_dfs = {}
        for section in doc:
            data = doc.get(section, {})
            data = [{"id": k, **v} for k, v in data.items()]
            df = pd.DataFrame(data)
            df = df.loc[df["tested"]]
            df = df.assign(
                supported=df["supported"].map({True: "✅", False: "❌"}),
                id=df["id"].str.replace("_", "-").str.upper(),
                title=df["title"].str.title(),
            ).drop(columns=["tested"])
            if not df.empty:
                print("\n" + "=" * 24)
                print()
                print(section)
                print()
                print(
                    df.assign(
                        description=df["description"].str.wrap(25),
                        code=df["code"].str.wrap(25),
                    ).to_markdown(index=False, tablefmt="rounded_grid")
                )
                section_dfs[section] = df
        if section_dfs:
            update_markdown(section_dfs, "../docs/features/index.md")
            update_markdown(
                section_dfs, "../README.md"
            )  # Consider changing to "../../README.md" if needed
        print()
        print()


def update_features_toml(support_results) -> TOMLDocument | None:
    """
    Update features.toml with tested and supported status from test results.
    Only update title if name is provided
    """
    toml_path = "scripts/features.toml"
    if not os.path.exists(toml_path):
        print(f"Warning: {toml_path} not found, skipping TOML update.")
        return None

    with open(toml_path, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    # Build a mapping of code -> (section, key, entry)
    features_by_code = {}
    for section, section_table in doc.items():
        if not isinstance(section_table, dict):
            continue
        for key, entry in section_table.items():
            code = key.replace("_", "-").upper()
            features_by_code[code] = (section, key, entry)

    # Mark all as untested and unsupported by default
    for code, (section, key, entry) in features_by_code.items():
        entry["tested"] = False
        entry["supported"] = False

    # Update tested features
    for result in support_results:
        code = result.feature_code.lstrip("#").upper()
        if code in features_by_code:
            section, key, entry = features_by_code[code]
            entry["tested"] = True
            entry["supported"] = bool(result.supported)
            # Only update title if name is provided and not empty
            if getattr(result, "name", None) and result.name:
                entry["title"] = result.name
        else:
            pass

    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
    print(f"Updated tested status in {toml_path}")
    return doc
