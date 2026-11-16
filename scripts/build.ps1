$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
$dataSource = Join-Path $projectRoot "data"
$assetSource = Join-Path $projectRoot "assets"
& $python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name SmartRacingChampionship --paths src --add-data "$dataSource;data" --add-data "$assetSource;assets" `
    --specpath build src/smart_racing/__main__.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built dist/SmartRacingChampionship.exe"
