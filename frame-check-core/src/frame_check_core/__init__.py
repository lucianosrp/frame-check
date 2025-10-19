"""
frame-check: A static column checker for dataframes!
"""

import argparse
from itertools import chain
import glob
from pathlib import Path
import sys
from typing import cast

from .config import Config, matching_files
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
        help="Python files (file.py), directories (dir/) or glob patterns (dir/**/*.py) to check. Directories will be searched recursively by default.",
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
        help="Files (file.py), directories (dir/) or glob patterns (dir/**/*.py) to ignore during checking.",
        default=[],
    )
    parser.add_argument(
        "--nonrecursive",
        "-n",
        action="store_true",
        help="Do not recursively check directories for Python files.",
        default=False,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to a configuration file (if not specified, configuration will be read frame-check.toml or pyproject.toml, if present)."
    )

    return parser


def collect_python_files(paths: list[str], config: Config) -> list[Path]:
    """Collect all Python files from the given paths.

    Args:
        paths: List of file paths, directory paths, or glob patterns.
        config: Config object with exclusion patterns.

    Returns:
        List of Path objects for Python files to check.
    """
    collected_files = set(
        chain.from_iterable(
            matching_files(path, config.recursive, config.should_exclude)
            for path in paths
        )
    )



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

    if not args.files:
        parser.print_help(sys.stderr)
        return 0

    if args.config:
        try:
            config = Config.load_from(args.config)
        except Exception as e:
            ...

    if args.ignore:
        cast(set, config.exclude).update(args.ignore)

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
