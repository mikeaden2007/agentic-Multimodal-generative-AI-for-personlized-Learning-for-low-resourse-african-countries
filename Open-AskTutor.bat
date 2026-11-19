@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT=%CD%"
set "PYTHON=%PROJECT%\.venv\Scripts\python.exe"
set "API_PORT=18137"
set "WEB_PORT=15637"
title Ask Tutor Startup
 echo ==================================================
 echo Ask Tutor - Starting from: %PROJECT%
 echo ==================================================
if not exist "%PYTHON%" (
 echo [1/4] Creating Python environment...
 where py >nul 2>nul
 if not errorlevel 1 (
   py -3 -m venv .venv
 ) else (
   python -m venv .venv
 )
 if errorlevel 1 goto :setup_error
)
if not exist "%PYTHON%" goto :setup_error
 echo [2/4] Checking Python dependencies...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :deps_error
 echo [3/4] Checking API imports...
"%PYTHON%" -c "import app.main, uvicorn"
if errorlevel 1 goto :import_error
 echo [4/4] Starting API and website...
start "Ask Tutor API" /D "%PROJECT%" cmd /k ""%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT%"
start "Ask Tutor Website" /D "%PROJECT%" cmd /k ""%PYTHON%" -m http.server %WEB_PORT% --bind 127.0.0.1 --directory frontend"
powershell -NoProfile -Command "$ok=$false;for($i=0;$i -lt 45;$i++){try{$a=Invoke-RestMethod -TimeoutSec 2 http://127.0.0.1:18137/openapi.json;$b=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:15637/dashboard.html;if($a.paths.PSObject.Properties.Name -contains '/teacher-agent/turn' -and $b.StatusCode -eq 200){$ok=$true;break}}catch{};Start-Sleep -Seconds 1};if($ok){exit 0}else{exit 1}"
if errorlevel 1 goto :server_error
 echo API and website responding.
start "" "http://127.0.0.1:15637/login.html"
echo Leave the API and Website windows open while using Ask Tutor.
pause
exit /b 0
:setup_error
echo ERROR: Could not create .venv. Install Python 3 and ensure it is on PATH.
goto :failed
:deps_error
echo ERROR: Python packages could not be installed. See output above.
goto :failed
:import_error
echo ERROR: Ask Tutor API could not import. See traceback above.
goto :failed
:server_error
echo ERROR: API or website failed to respond. Check the two server windows for errors.
goto :failed
:failed
pause
exit /b 1
