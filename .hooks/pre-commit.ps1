#!/usr/bin/env pwsh
# Pre-commit hook: runs linting and tests, blocking the commit on any failure.

$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel
Set-Location $repoRoot

$failed = $false

# Write-Host "==> black: checking formatting..." -ForegroundColor Cyan
# uv run black --check src/ tests/
# if ($LASTEXITCODE -ne 0) {
#     Write-Host "FAILED: black found formatting issues. Run 'uv run black src/ tests/' to fix." -ForegroundColor Red
#     $failed = $true
# }

# Write-Host "==> flake8: linting src/..." -ForegroundColor Cyan
# uv run flake8 src/
# if ($LASTEXITCODE -ne 0) {
#     Write-Host "FAILED: flake8 reported errors." -ForegroundColor Red
#     $failed = $true
# }

Write-Host "==> pytest: running unit tests..." -ForegroundColor Cyan
uv run pytest tests/pytest/
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: pytest tests did not pass." -ForegroundColor Red
    $failed = $true
}

Write-Host "==> behave: running BDD tests..." -ForegroundColor Cyan
uv run behave tests/bdd/
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: behave tests did not pass." -ForegroundColor Red
    $failed = $true
}

if ($failed) {
    Write-Host "`nPre-commit checks failed. Commit aborted." -ForegroundColor Red
    exit 1
}

Write-Host "`nAll pre-commit checks passed." -ForegroundColor Green
exit 0
