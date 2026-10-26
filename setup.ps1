$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m venv .venv
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
Write-Host 'Setup complete. Starting the webcam monitor; press q or Esc to quit.'
& $python main.py @args
exit $LASTEXITCODE
