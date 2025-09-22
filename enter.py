#!/bin/python3
"""
Script to check minimum requirements to enter the sprint
"""

import os
import subprocess
import sys

import psutil

BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
MIN_UV_MINOR_VERSION = 8

print(f"{BOLD}Welcome! Checking sprint requirements...{RESET}")

# Track errors for final report
errors = []


def test_has_git():
    """Check if the user has git installed"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{RED}❌ git is not installed{RESET}")
            errors.append("git_not_installed")
            return False
        print(f"{GREEN}✅ git is installed{RESET}")
        return True
    except FileNotFoundError:
        print(f"{RED}❌ git is not installed{RESET}")
        errors.append("git_not_installed")
        return False


def test_has_uv():
    """Check if the user has uv installed"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{RED}❌ uv is not installed{RESET}")
            errors.append("uv_not_installed")
            return False

        version_output = result.stdout.strip()
        print(f"{GREEN}✅ uv is installed{RESET}")

        # Store the version
        try:
            minor_ver = version_output.split()[1].split(".")[1]
            if int(minor_ver) < MIN_UV_MINOR_VERSION:
                print(f"{RED}❌ uv version is too old: {version_output}{RESET}")
                errors.append("uv_outdated")
                return False
        except (ValueError, IndexError):
            print(f"{RED}❌ uv version is invalid: {version_output}{RESET}")
            errors.append("uv_invalid_version")
            return False
        return True
    except FileNotFoundError:
        print(f"{RED}❌ uv is not installed{RESET}")
        errors.append("uv_not_installed")
        return False


def test_has_python_3_12():
    """Check if the user has python installed"""
    try:
        python_version = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        )
        if python_version.returncode != 0:
            print(f"{GREEN}✅ python is installed{RESET}")

            # Check if Python version is at least 3.12
            version_output = python_version.stdout.strip()
            try:
                version_parts = version_output.split()[1].split(".")
                major_ver = int(version_parts[0])
                minor_ver = int(version_parts[1])
                if major_ver < 3 or (major_ver == 3 and minor_ver < 12):
                    print(f"{RED}❌ Python version is too old: {version_output}{RESET}")
                    errors.append("python_outdated")
                    return False
            except (ValueError, IndexError):
                print(f"{RED}❌ Python version is invalid: {version_output}{RESET}")
                errors.append("python_invalid_version")
                return False
            return True

        print(f"{GREEN}✅ python is installed{RESET}")

        # Check if Python version is at least 3.12
        version_output = python_version.stdout.strip()
        try:
            version_parts = version_output.split()[1].split(".")
            major_ver = int(version_parts[0])
            minor_ver = int(version_parts[1])
            if major_ver < 3 or (major_ver == 3 and minor_ver < 12):
                print(f"{RED}❌ Python version is too old: {version_output}{RESET}")
                errors.append("python_outdated")
                return False
        except (ValueError, IndexError):
            print(f"{RED}❌ Python version is invalid: {version_output}{RESET}")
            errors.append("python_invalid_version")
            return False
        return True
    except FileNotFoundError:
        print(f"{GREEN}✅ python is installed{RESET}")

        # Check if Python version is at least 3.12
        version_output = sys.version
        try:
            version_parts = version_output.split()[0].split(".")
            major_ver = int(version_parts[0])
            minor_ver = int(version_parts[1])
            if major_ver < 3 or (major_ver == 3 and minor_ver < 12):
                print(f"{RED}❌ Python version is too old: {sys.version}{RESET}")
                errors.append("python_outdated")
                return False
        except (ValueError, IndexError):
            print(f"{RED}❌ Python version is invalid: {sys.version}{RESET}")
            errors.append("python_invalid_version")
            return False
        return True


def test_specs():
    """Minimum 4 CPU cores, 4GB RAM, Python 3.12"""
    cpu_count = os.cpu_count()
    memory_info = psutil.virtual_memory()

    # Check CPU cores
    if (cpu_count or 0) < 4:
        print(
            f"{RED}❌ CPU cores are too low: {cpu_count or 0} cores (minimum 4 required){RESET}"
        )
        errors.append("insufficient_cpu")
        return False
    print(f"{GREEN}✅ CPU cores sufficient: {cpu_count} cores{RESET}")

    # Check RAM
    if memory_info.total < 4 * 1024 * 1024 * 1024:
        ram_gb = memory_info.total / (1024 * 1024 * 1024)
        print(f"{RED}❌ RAM is too low: {ram_gb:.1f} GB (minimum 4 GB required){RESET}")
        errors.append("insufficient_ram")
        return False
    ram_gb = memory_info.total / (1024 * 1024 * 1024)
    print(f"{GREEN}✅ RAM sufficient: {ram_gb:.1f} GB{RESET}")
    return True


def print_solutions():
    """Print solutions for all encountered errors"""
    if not errors:
        print(
            f"\n{GREEN}{BOLD}🎉 All requirements met! You're ready for the sprint!{RESET}"
        )
        return

    print(f"\n{YELLOW}{BOLD}📋 Solutions for encountered issues:{RESET}")
    print("=" * 50)

    if "git_not_installed" in errors:
        print(f"\n{BOLD}Git not installed:{RESET}")
        print("• Ubuntu/Debian: sudo apt-get install git")
        print("• macOS: brew install git (or install Xcode Command Line Tools)")
        print("• Windows: Download from https://git-scm.com/download/win")

    if "uv_not_installed" in errors:
        print(f"\n{BOLD}uv not installed:{RESET}")
        print("• Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print(
            '• Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
        print("• Or with pip: pip install uv")

    if "uv_outdated" in errors:
        print(f"\n{BOLD}uv version too old:{RESET}")
        print("• Update uv: uv self update")
        print("• Or reinstall: curl -LsSf https://astral.sh/uv/install.sh | sh")

    if "uv_invalid_version" in errors:
        print(f"\n{BOLD}uv version invalid:{RESET}")
        print("• Reinstall uv: curl -LsSf https://astral.sh/uv/install.sh | sh")

    if "python_outdated" in errors:
        print(f"\n{BOLD}Python version too old:{RESET}")
        print("• With uv (recommended): uv python install 3.12")
        print("• Or install Python 3.12+ from https://www.python.org/downloads/")

    if "python_invalid_version" in errors:
        print(f"\n{BOLD}Python version invalid:{RESET}")
        print("• Reinstall Python 3.12+ from https://www.python.org/downloads/")
        print("• Or with uv: uv python install 3.12")

    if "insufficient_cpu" in errors:
        print(f"\n{BOLD}Insufficient CPU cores:{RESET}")
        print("• This sprint requires at least 4 CPU cores")
        print("• Consider upgrading your hardware or using a cloud instance")
        print("• Cloud options: AWS EC2, Google Cloud Compute, Azure VMs")

    if "insufficient_ram" in errors:
        print(f"\n{BOLD}Insufficient RAM:{RESET}")
        print("• This sprint requires at least 4 GB of RAM")
        print("• Consider upgrading your hardware or using a cloud instance")
        print("• Close other applications to free up memory")

    print(
        f"\n{YELLOW}After fixing these issues, run this script again to verify.{RESET}"
    )


if __name__ == "__main__":
    all_passed = True

    all_passed &= test_specs()
    all_passed &= test_has_git()
    all_passed &= test_has_uv()
    all_passed &= test_has_python_3_12()

    print_solutions()

    if not all_passed:
        sys.exit(1)
