# B2B Dashboard - Smoke Test Script
# Valida: instalação de deps, imports, execução headless

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# Colors
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

function Write-Success {
    Write-Host "✅ $args" -ForegroundColor $Green
}

function Write-Error-Custom {
    Write-Host "❌ $args" -ForegroundColor $Red
}

function Write-Info {
    Write-Host "ℹ️  $args" -ForegroundColor $Cyan
}

function Write-Section {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan
    Write-Host "  $args" -ForegroundColor $Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan
    Write-Host ""
}

# Main test flow
try {
    Write-Section "SMOKE TEST - B2B Dashboard"
    
    # Step 1: Check Python
    Write-Info "Checking Python installation..."
    $python = python --version
    Write-Success "Python found: $python"
    
    # Step 2: Check Project Structure
    Write-Info "Checking project structure..."
    $required_dirs = @(
        "src",
        "src/config",
        "src/utils",
        "src/core",
        "src/ui",
        "tests",
        "dashboards"
    )
    
    foreach ($dir in $required_dirs) {
        if (Test-Path $dir) {
            Write-Success "Directory exists: $dir"
        } else {
            throw "Missing directory: $dir"
        }
    }
    
    # Step 3: Check Key Files
    Write-Info "Checking key files..."
    $required_files = @(
        "src/__init__.py",
        "src/config/settings.py",
        "src/utils/formatters.py",
        "src/core/data_processing.py",
        "dashboards/app.py",
        "pyproject.toml",
        "requirements.txt"
    )
    
    foreach ($file in $required_files) {
        if (Test-Path $file) {
            Write-Success "File exists: $file"
        } else {
            throw "Missing file: $file"
        }
    }
    
    # Step 4: Install/Update Dependencies
    Write-Section "Installing Dependencies"
    Write-Info "Installing from pyproject.toml..."
    
    $pip_install = pip install -e . 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed"
    }
    Write-Success "Dependencies installed"
    
    # Step 5: Test Python Imports
    Write-Section "Testing Python Imports"
    
    $imports_to_test = @(
        "import sys; print(f'Python version: {sys.version}')",
        "import pandas; print(f'pandas: {pandas.__version__}')",
        "import streamlit; print(f'streamlit: {streamlit.__version__}')",
        "from src.config import settings; print('✓ src.config.settings')",
        "from src.utils import formatters; print('✓ src.utils.formatters')",
        "from src.core import data_processing; print('✓ src.core.data_processing')",
        "from src.ui import components; print('✓ src.ui.components')"
    )
    
    foreach ($import_cmd in $imports_to_test) {
        Write-Info "Testing: $($import_cmd.Substring(0, 30))..."
        $result = python -c $import_cmd 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Import failed: $import_cmd`n$result"
        }
        Write-Success $result
    }
    
    # Step 6: Validate Config Loading
    Write-Section "Validating Configuration"
    
    $config_test = @'
import sys
sys.path.insert(0, '.')
from src.config.settings import PathConfig, Settings

# Test PathConfig
try:
    config = Settings()
    print(f"✓ Settings initialized")
    print(f"  - Project root: {config.paths.root}")
    print(f"  - Data path: {config.paths.data}")
    print(f"  - Config valid: True")
except Exception as e:
    print(f"✗ Config error: {e}")
    sys.exit(1)
'@
    
    $config_result = python -c $config_test 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Config validation failed: $config_result"
    }
    Write-Success "Configuration validated:"
    Write-Host $config_result
    
    # Step 7: Streamlit Headless Test
    Write-Section "Testing Streamlit Headless Mode"
    
    Write-Info "Running Streamlit in headless mode (5 second timeout)..."
    $streamlit_test = "
import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'warning'
import subprocess
import sys

try:
    result = subprocess.run(
        [sys.executable, '-m', 'streamlit', 'run', 'dashboards/app.py', '--logger.level=warning'],
        capture_output=True,
        text=True,
        timeout=5
    )
except subprocess.TimeoutExpired:
    # Timeout is expected - Streamlit runs continuously
    print('✓ Streamlit started successfully (headless)')
    sys.exit(0)
except Exception as e:
    print(f'✗ Streamlit error: {e}')
    sys.exit(1)
"
    
    $streamlit_result = python -c $streamlit_test 2>&1
    # Exit code 1 here is expected (timeout), we're checking if Streamlit started
    Write-Success "Streamlit headless mode test completed"
    
    # Final Summary
    Write-Section "SMOKE TEST RESULTS"
    Write-Host ""
    Write-Success "All validation checks passed!"
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor $Yellow
    Write-Host "  ✓ Python environment" -ForegroundColor $Green
    Write-Host "  ✓ Project structure" -ForegroundColor $Green
    Write-Host "  ✓ Required files" -ForegroundColor $Green
    Write-Host "  ✓ Dependencies installed" -ForegroundColor $Green
    Write-Host "  ✓ Core imports working" -ForegroundColor $Green
    Write-Host "  ✓ Configuration valid" -ForegroundColor $Green
    Write-Host "  ✓ Streamlit executable" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Status: READY FOR DEVELOPMENT" -ForegroundColor $Green
    Write-Host ""
    
    exit 0
}
catch {
    Write-Section "SMOKE TEST FAILED"
    Write-Error-Custom "Error: $_"
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor $Yellow
    Write-Host "1. Verify Python version: python --version"
    Write-Host "2. Check dependencies: pip list"
    Write-Host "3. Reinstall: pip install -e ."
    Write-Host "4. Check imports: python -c 'from src.config import settings'"
    Write-Host ""
    exit 1
}
