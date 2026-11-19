$ErrorActionPreference = "Stop"

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"

Set-Location $project

$existing = Get-NetTCPConnection `
    -LocalPort 8000 `
    -State Listen `
    -ErrorAction SilentlyContinue

if ($existing) {
    Write-Host "AskTutor is already running on port 8000."
    Write-Host "No additional server will be started."
    exit
}

Write-Host "Starting AskTutor recovery server..."
Write-Host "Project: $project"

& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
