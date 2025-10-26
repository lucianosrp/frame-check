"""Generate feature documentation pages from the features.toml file."""

import re
import tomllib
from pathlib import Path

import mkdocs_gen_files
from mkdocs_gen_files.nav import Nav


def snake_to_title_case(s):
    """Convert snake_case to Title Case with spaces."""
    return " ".join(word.capitalize() for word in s.split("_"))


# Create navigation for mkdocs-literate-nav
nav = Nav()

# Load the features.toml file
features_file = Path(__file__).parent / "features.toml"
with open(features_file, "rb") as f:
    features_data = tomllib.load(f)

# Create the root "features" entry in the navigation
nav[("Features",)] = "index.md"

# Generate a markdown file for each top-level section
for section_name, section_content in features_data.items():
    # Prepare section title
    section_title = snake_to_title_case(section_name)

    # Start with the section header
    content = [f"# {section_title}\n\n"]

    # Sort items by their keys to maintain order
    sorted_items = sorted(
        section_content.items(),
        key=lambda x: tuple(int(n) if n.isdigit() else n for n in x[0].split("_")),
    )

    # Add each feature to the content
    for item_key, item_data in sorted_items:
        # Extract the item code (like 'dcms_1' from the key)
        item_code_match = re.search(r"([a-z]+)_(\d+)", item_key)
        if item_code_match:
            prefix = item_code_match.group(1).upper()
            number = item_code_match.group(2)
            item_code = f"{prefix}-{number}"
        else:
            item_code = item_key.upper()

        # Add the item header and content
        content.append(f"## {item_code}: {item_data['title']}\n")
        content.append("```python\n" + item_data["code"] + "\n```\n")
        content.append(item_data["description"] + "\n\n")
        content.append(item_data["description"] + "\n\n")

    # Write the content to a markdown file using mkdocs_gen_files
    doc_path = Path("features", f"{section_name}.md")
    with mkdocs_gen_files.open(doc_path, "w") as f:
        f.write("".join(content))

    # Set edit path to point to the original features.toml file
    mkdocs_gen_files.set_edit_path(
        doc_path, features_file.relative_to(Path(__file__).parent.parent)
    )

    # Add to navigation under "Features"
    nav[("Features", section_title)] = doc_path.as_posix()

# Generate index page
index_content = ["# Pandas Features\n\n"]
index_content.append(
    "Frame-check supports various pandas features and usage patterns:\n\n"
)

for section_name, section_content in features_data.items():
    section_title = snake_to_title_case(section_name)
    index_content.append(f"- [{section_title}]({section_name}.md)\n")

index_path = Path("features", "index.md")
with mkdocs_gen_files.open(index_path, "w") as f:
    f.write("".join(index_content))

mkdocs_gen_files.set_edit_path(
    index_path, features_file.relative_to(Path(__file__).parent.parent)
)

# Create SUMMARY.md for literate navigation
with mkdocs_gen_files.open("summary.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
