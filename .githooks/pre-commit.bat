@echo off
REM Pre-commit hook para detectar secretos (Windows batch version)
REM Este hook se ejecuta antes de cada commit para validar que no hay secretos

for /f "delims=" %%i in ('git rev-parse --show-toplevel') do set REPO_ROOT=%%i

set VALIDATE_SCRIPT=%REPO_ROOT%\scripts\validate-secrets.py

if not exist "%VALIDATE_SCRIPT%" (
    echo ❌ Error: No se encontró el script de validación en %VALIDATE_SCRIPT%
    exit /b 1
)

REM Intentar usar Python del venv del proyecto
if exist "%REPO_ROOT%\.venv\Scripts\python.exe" (
    "%REPO_ROOT%\.venv\Scripts\python.exe" "%VALIDATE_SCRIPT%"
    exit /b %ERRORLEVEL%
)

REM Intentar usar py (Windows Python launcher)
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py "%VALIDATE_SCRIPT%"
    exit /b %ERRORLEVEL%
)

REM Intentar usar python
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%VALIDATE_SCRIPT%"
    exit /b %ERRORLEVEL%
)

echo ❌ Error: No se encontró Python en el sistema
exit /b 1