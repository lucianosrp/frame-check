#Requires -Version 5.1

$MIN_UV_MINOR = 8

Write-Host "Welcome! Checking sprint requirements..." -ForegroundColor White

$errors = @()

function Test-HasGit {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "✅ git is installed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ git is not installed" -ForegroundColor Red
        $script:errors += "git_not_installed"
        return $false
    }
}

function Test-HasUv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $versionOutput = uv --version
        $version = $versionOutput.Split()[1]
        Write-Host "✅ uv is installed" -ForegroundColor Green
        $minor = [int]$version.Split('.')[1]
        if ($minor -lt $MIN_UV_MINOR) {
            Write-Host "❌ uv version is too old: $version" -ForegroundColor Red
            $script:errors += "uv_outdated"
            return $false
        }
        return $true
    } else {
        Write-Host "❌ uv is not installed" -ForegroundColor Red
        $script:errors += "uv_not_installed"
        return $false
    }
}

function Test-HasPython312 {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $versionOutput = python --version 2>&1
        $version = $versionOutput.Split()[1]
        Write-Host "✅ python is installed" -ForegroundColor Green
        $major = [int]$version.Split('.')[0]
        $minor = [int]$version.Split('.')[1]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
            Write-Host "❌ Python version is too old: $version" -ForegroundColor Red
            $script:errors += "python_outdated"
            return $false
        }
        return $true
    } else {
        Write-Host "❌ python is not installed" -ForegroundColor Red
        $script:errors += "python_not_installed"
        return $false
    }
}

function Test-Specs {
    $cpu = (Get-WmiObject Win32_Processor).NumberOfLogicalProcessors
    $ramGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
    if ($cpu -lt 4) {
        Write-Host "❌ CPU cores are too low: $cpu cores (minimum 4 required)" -ForegroundColor Red
        $script:errors += "insufficient_cpu"
        return $false
    }
    Write-Host "✅ CPU cores sufficient: $cpu cores" -ForegroundColor Green
    if ($ramGB -lt 4) {
        Write-Host "❌ RAM is too low: $ramGB GB (minimum 4 GB required)" -ForegroundColor Red
        $script:errors += "insufficient_ram"
        return $false
    }
    Write-Host "✅ RAM sufficient: $ramGB GB" -ForegroundColor Green
    return $true
}

function Print-Solutions {
    if ($errors.Count -eq 0) {
        Write-Host "`n🎉 All requirements met! You're ready for the sprint!" -ForegroundColor Green
        return
    }
    Write-Host "`n📋 Solutions for encountered issues:" -ForegroundColor Yellow
    Write-Host ("=" * 50)
    foreach ($error in $errors) {
        switch ($error) {
            "git_not_installed" {
                Write-Host "`nGit not installed:"
                Write-Host "• Ubuntu/Debian: sudo apt-get install git"
                Write-Host "• macOS: brew install git (or install Xcode Command Line Tools)"
                Write-Host "• Windows: Download from https://git-scm.com/download/win"
            }
            "uv_not_installed" {
                Write-Host "`nuv not installed:"
                Write-Host "• Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
                Write-Host '• Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
                Write-Host "• Or with pip: pip install uv"
            }
            "uv_outdated" {
                Write-Host "`nuv version too old:"
                Write-Host "• Update uv: uv self update"
                Write-Host "• Or reinstall: curl -LsSf https://astral.sh/uv/install.sh | sh"
            }
            "python_outdated" {
                Write-Host "`nPython version too old:"
                Write-Host "• With uv (recommended): uv python install 3.12"
                Write-Host "• Or install Python 3.12+ from https://www.python.org/downloads/"
            }
            "python_not_installed" {
                Write-Host "`nPython not installed:"
                Write-Host "• Install Python 3.12+ from https://www.python.org/downloads/"
                Write-Host "• Or with uv: uv python install 3.12"
            }
            "insufficient_cpu" {
                Write-Host "`nInsufficient CPU cores:"
                Write-Host "• This sprint requires at least 4 CPU cores"
                Write-Host "• Consider upgrading your hardware or using a cloud instance"
                Write-Host "• Cloud options: AWS EC2, Google Cloud Compute, Azure VMs"
            }
            "insufficient_ram" {
                Write-Host "`nInsufficient RAM:"
                Write-Host "• This sprint requires at least 4 GB of RAM"
                Write-Host "• Consider upgrading your hardware or using a cloud instance"
                Write-Host "• Close other applications to free up memory"
            }
        }
    }
    Write-Host "`nAfter fixing these issues, run this script again to verify." -ForegroundColor Yellow
}

$allPassed = $true
if (!(Test-Specs)) { $allPassed = $false }
if (!(Test-HasGit)) { $allPassed = $false }
if (!(Test-HasUv)) { $allPassed = $false }
if (!(Test-HasPython312)) { $allPassed = $false }

Print-Solutions

if (!$allPassed) {
    exit 1
}
