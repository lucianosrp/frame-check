"""
frame-check: A static column checker for dataframes!
"""

import argparse
import glob
import sys
from pathlib import Path
from typing import cast

from frame_check_core.config import Config

from .frame_checker import FrameChecker
from .util.message import print_diagnostics


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for frame-check CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="frame-check",
        description="A static checker for dataframes!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Python files, directories, or glob patterns to check. ",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        nargs="+",
        help="Files to ignore during checking (e.g. test.py)",
        default=[],
    )

    return parser


def collect_python_files(paths: list[str], config: Config) -> list[Path]:
    """Collect all Python files from the given paths.

    Args:
        paths: List of file paths, directory paths, or glob patterns.
               If empty, defaults to all .py files in current directory recursively.
        config: Config object with exclusion patterns.

    Returns:
        List of Path objects for Python files to check.
    """

    if not paths:
        # Default: all .py files in current directory and subdirectories (recursive)
        all_files = sorted(Path(p) for p in Path.cwd().rglob("*.py"))
        # Filter out excluded files using fast prefix checking
        result = [f for f in all_files if not config.should_exclude(f)]
        return result

    collected_files: set[Path] = set()

    for path_str in paths:
        path = Path(path_str)

        if path.is_file() and path.suffix == ".py":
            collected_files.add(path.resolve())
        elif path.is_dir():
            # Recursively find all .py files in the directory
            collected_files.update(path.rglob("*.py"))
        else:
            # treat as a glob pattern
            for matched_path in glob.glob(path_str, recursive=True):
                matched = Path(matched_path)
                if matched.is_file() and matched.suffix == ".py":
                    collected_files.add(matched.resolve())

    # Filter out excluded files using fast prefix checking
    result = sorted(f for f in collected_files if not config.should_exclude(f))
    return result


def main(argv: list[str] | None = None, config: Config | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    config = Config()  # Default configuration

    if (frame_check_settings := Path.cwd() / "frame-check.toml").exists():
        config = Config.load_from(frame_check_settings)

    elif (pyproject_settings := Path.cwd() / "pyproject.toml").exists():
        config = Config.load_from(pyproject_settings)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 0

    if args.ignore:
        cast(set, config.exclude).update(args.ignore)

    # Collect all Python files to check
    python_files = collect_python_files(args.files, config=config)

    if not python_files:
        print("No Python files found to check.", file=sys.stderr)
        return 0

    # Track if any file has diagnostics
    has_errors = False

    # Process each file
    for file_path in python_files:
        try:
            fc = FrameChecker.check(file_path)
            if fc.diagnostics:
                has_errors = True
                print_diagnostics(fc, str(file_path))

        except SyntaxError as e:
            print(f"Syntax error in {file_path}:\n{e}", file=sys.stderr)
            has_errors = True
        except Exception as e:
            print(f"Error checking {file_path}:\n{e}", file=sys.stderr)
            has_errors = True

    return 1 if has_errors else 0
