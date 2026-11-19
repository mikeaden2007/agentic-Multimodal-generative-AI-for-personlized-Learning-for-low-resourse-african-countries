param([switch]$InstallDependencies)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $project
$python = Join-Path $project '.venv\Scripts\python.exe'
Write-Host "Ask Tutor project: $project" -ForegroundColor Cyan
if (!(Test-Path $python)) {
  Write-Host 'Project virtual environment is missing. Create it with: py -3.12 -m venv .venv' -ForegroundColor Red
  exit 1
}
$actual = (& $python -c 'import sys; print(sys.executable)' 2>&1 | Out-String).Trim()
Write-Host "Using Python: $actual"
if ($actual -notlike "$project\*") {
  Write-Host 'ERROR: Python executable is not in this project. Recreate .venv in this folder.' -ForegroundColor Red
  exit 1
}
if ($InstallDependencies) {
  Write-Host 'Installing pinned project dependencies from requirements.txt...' -ForegroundColor Yellow
  & $python -m pip install -r (Join-Path $project 'requirements.txt')
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$check = @'
import importlib
mods = ['fastapi','uvicorn','sklearn','requests','pydantic','pytesseract','PIL','pymupdf','docx','multipart','sympy']
missing = []
for name in mods:
    try: importlib.import_module(name)
    except Exception as exc: missing.append(f'{name}: {exc}')
if missing:
    print('MISSING OR BROKEN DEPENDENCIES:')
    print('\n'.join(missing))
    raise SystemExit(2)
print('All required Python imports passed.')
'@
& $python -c $check
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Run this ONCE to install/repair packages: .\Start-AskTutor.ps1 -InstallDependencies' -ForegroundColor Yellow
  exit 2
}
$existing = @(Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue)
if ($existing.Count -gt 0) {
  $pids = @($existing | Select-Object -ExpandProperty OwningProcess -Unique)
  foreach ($pidNumber in $pids) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $pidNumber" -ErrorAction SilentlyContinue
    Write-Host "Port 8001 already in use. PID=$pidNumber, command=$($proc.CommandLine)" -ForegroundColor Yellow
  }
  Write-Host 'Do not start a second server. To apply new code, stop the confirmed old port-8001 Uvicorn process first, then rerun this script.' -ForegroundColor Yellow
  exit 3
}
Write-Host 'Starting Ask Tutor at http://127.0.0.1:8001' -ForegroundColor Green
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
exit $LASTEXITCODE
