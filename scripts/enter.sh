#!/bin/bash

BOLD="\033[1m"
GREEN="\033[92m"
RED="\033[91m"
YELLOW="\033[93m"
RESET="\033[0m"
MIN_UV_MINOR=8

echo -e "${BOLD}Welcome! Checking sprint requirements...${RESET}"

errors=()

function test_has_git() {
    if command -v git >/dev/null 2>&1; then
        echo -e "${GREEN}✅ git is installed${RESET}"
        return 0
    else
        echo -e "${RED}❌ git is not installed${RESET}"
        errors+=("git_not_installed")
        return 1
    fi
}

function test_has_uv() {
    if command -v uv >/dev/null 2>&1; then
        version=$(uv --version | awk '{print $2}')
        echo -e "${GREEN}✅ uv is installed${RESET}"
        minor=$(echo $version | cut -d. -f2)
        if [ "$minor" -lt "$MIN_UV_MINOR" ]; then
            echo -e "${RED}❌ uv version is too old: $version${RESET}"
            errors+=("uv_outdated")
            return 1
        fi
        return 0
    else
        echo -e "${RED}❌ uv is not installed${RESET}"
        errors+=("uv_not_installed")
        return 1
    fi
}

function test_has_python_3_12() {
    if command -v python3 >/dev/null 2>&1; then
        version=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✅ python is installed${RESET}"
        major=$(echo $version | cut -d. -f1)
        minor=$(echo $version | cut -d. -f2)
        if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 12 ]); then
            echo -e "${RED}❌ Python version is too old: $version${RESET}"
            errors+=("python_outdated")
            return 1
        fi
        return 0
    else
        echo -e "${RED}❌ python is not installed${RESET}"
        errors+=("python_not_installed")
        return 1
    fi
}

function test_specs() {
    os=$(uname)
    if [ "$os" = "Darwin" ]; then
        cpu=$(sysctl -n hw.ncpu)
        ram=$(sysctl -n hw.memsize | awk '{print int($0/1024/1024/1024)}')
    else
        cpu=$(nproc)
        ram=$(free -g | awk 'NR==2{print $2}')
    fi
    if [ "$cpu" -lt 4 ]; then
        echo -e "${RED}❌ CPU cores are too low: $cpu cores (minimum 4 required)${RESET}"
        errors+=("insufficient_cpu")
        return 1
    fi
    echo -e "${GREEN}✅ CPU cores sufficient: $cpu cores${RESET}"
    if [ "$ram" -lt 4 ]; then
        echo -e "${RED}❌ RAM is too low: $ram GB (minimum 4 GB required)${RESET}"
        errors+=("insufficient_ram")
        return 1
    fi
    echo -e "${GREEN}✅ RAM sufficient: $ram GB${RESET}"
    return 0
}

function print_solutions() {
    if [ ${#errors[@]} -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}🎉 All requirements met! You're ready for the sprint!${RESET}"
        return
    fi
    echo -e "\n${YELLOW}${BOLD}📋 Solutions for encountered issues:${RESET}"
    echo "=================================================="
    for error in "${errors[@]}"; do
        case $error in
            git_not_installed)
                echo -e "\n${BOLD}Git not installed:${RESET}"
                echo "• Ubuntu/Debian: sudo apt-get install git"
                echo "• macOS: brew install git (or install Xcode Command Line Tools)"
                echo "• Windows: Download from https://git-scm.com/download/win"
                ;;
            uv_not_installed)
                echo -e "\n${BOLD}uv not installed:${RESET}"
                echo "• Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
                echo '• Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
                echo "• Or with pip: pip install uv"
                ;;
            uv_outdated)
                echo -e "\n${BOLD}uv version too old:${RESET}"
                echo "• Update uv: uv self update"
                echo "• Or reinstall: curl -LsSf https://astral.sh/uv/install.sh | sh"
                ;;
            python_outdated)
                echo -e "\n${BOLD}Python version too old:${RESET}"
                echo "• With uv (recommended): uv python install 3.12"
                echo "• Or install Python 3.12+ from https://www.python.org/downloads/"
                ;;
            python_not_installed)
                echo -e "\n${BOLD}Python not installed:${RESET}"
                echo "• Install Python 3.12+ from https://www.python.org/downloads/"
                echo "• Or with uv: uv python install 3.12"
                ;;
            insufficient_cpu)
                echo -e "\n${BOLD}Insufficient CPU cores:${RESET}"
                echo "• This sprint requires at least 4 CPU cores"
                echo "• Consider upgrading your hardware or using a cloud instance"
                echo "• Cloud options: AWS EC2, Google Cloud Compute, Azure VMs"
                ;;
            insufficient_ram)
                echo -e "\n${BOLD}Insufficient RAM:${RESET}"
                echo "• This sprint requires at least 4 GB of RAM"
                echo "• Consider upgrading your hardware or using a cloud instance"
                echo "• Close other applications to free up memory"
                ;;
        esac
    done
    echo -e "\n${YELLOW}After fixing these issues, run this script again to verify.${RESET}"
}

all_passed=true
if ! test_specs; then all_passed=false; fi
if ! test_has_git; then all_passed=false; fi
if ! test_has_uv; then all_passed=false; fi
if ! test_has_python_3_12; then all_passed=false; fi

print_solutions

if ! $all_passed; then
    exit 1
fi
