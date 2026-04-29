#!/usr/bin/env pwsh
# Pre-commit hook: runs linting and tests, blocking the commit on any failure.

$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel
Set-Location $repoRoot

$fabricNotebookResourceScripts = @(
    @{
        script = 'src/data_wrangler/data_wrangler.py'
        notebooks = @(
            'fabric/Process To Silver.Notebook'
            'fabric/Project to Gold.Notebook'
        )
    }
)

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

# Ensure the fabric notebook resources are updated
Write-Host '==> Syncing Fabric Notebook Resources...' -ForegroundColor Cyan
try {
    foreach ($resource in $fabricNotebookResourceScripts) {
        $srcFile = Join-Path $repoRoot $resource.script
        foreach ($notebook in $resource.notebooks) {
            $destNotebookDir = Join-Path $repoRoot $notebook
            $destDir = Join-Path $destNotebookDir 'Resources/builtin/internal_classes'
            $destFile = Join-Path $destDir (Split-Path $srcFile -Leaf)
    
            $copied = $false
            if (-not (Test-Path $destFile)) {
                Copy-Item -Force $srcFile $destFile
                $copied = $true
            } elseif ((Get-FileHash $srcFile).Hash -ne (Get-FileHash $destFile).Hash) {
                Copy-Item -Force $srcFile $destFile
                $copied = $true
            }
    
            if ($copied) {
                Write-Host "==> Updated notebook resource: $destFile" -ForegroundColor Cyan
                git add "$destFile"
            }
        }
    }
    Write-Host 'Complete.' -f Green
}
catch {
    Write-Host "FAILED: Error whilst syncing Fabric Notebook Resources - $($_.Exception.Message)" -ForegroundColor Red
    $failed = $true
}

if ($failed) {
    Write-Host "`nPre-commit checks failed. Commit aborted." -ForegroundColor Red
    exit 1
}

Write-Host "`nAll pre-commit checks passed." -ForegroundColor Green
exit 0
