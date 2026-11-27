@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where python >nul 2>&1
    if errorlevel 1 goto python_error
    python -m venv .venv
    if errorlevel 1 goto error
)

.venv\Scripts\python.exe -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto error
)

echo Starting PolkaInsight...
echo Open http://localhost:8501 in your browser.
.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto error
goto end

:python_error
echo Python was not found. Install Python 3.12 or newer and add it to PATH.
pause
goto end

:error
echo PolkaInsight could not start. Check Python, the files and your internet connection.
pause

:end
endlocal
