$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
$dataSource = Join-Path $projectRoot "data"
& $python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name SmartRacingChampionship --paths src --add-data "$dataSource;data" `
    --specpath build src/smart_racing/__main__.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built dist/SmartRacingChampionship.exe"
