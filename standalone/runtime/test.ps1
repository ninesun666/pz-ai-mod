param([switch]$Build)
$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Push-Location $root
try {
    python -m unittest discover -s tests -p "test_standalone*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Standalone tests failed" }
    git diff --check
    if ($LASTEXITCODE -ne 0) { throw "Whitespace check failed" }
    if ($Build) {
        & "$PSScriptRoot\build.ps1"
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    }
    Write-Output "Standalone automated gate PASSED (not gameplay acceptance)."
} finally { Pop-Location }
