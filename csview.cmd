@echo off

REM For running `csview` at a Windows command prompt.
REM Requires Python 3 with `python` and `pip` to be available in the path.

set CALL_COMMAND=%~f0
set BASE_DIR=%~dp0
set CALL_STEM=%~n0
set PYTHON_SCRIPT="%CALL_STEM%.py"
set MYNAME=%CALL_COMMAND%
set MYPATH=%BASE_DIR%
set VENV_NAME="venv"
set VENV_HOME="%BASE_DIR%\%VENV_NAME%"
set VENV_SCRIPT="%VENV_HOME%\bin\activate.bat"
set VENV_DEACTIVATE="%VENV_HOME%\bin\deactivate.bat"
set DEPS_FILE="requirements.txt"
set DEPS_PATH="%BASE_DIR%\%DEPS_FILE%"

IF NOT EXIST "%VENV_SCRIPT%" (
    pip install -r requirements.txt
    python3 -m venv venv
)

IF NOT EXIST "%VENV_SCRIPT%" (
    echo "ERROR: could not find or create Python virtual environment in %VENV_HOME%"
    exit 1
)

IF NOT EXIST "%PYTHON_SCRIPT%" (
    echo "ERROR: could not find Python script: %PYTHON_SCRIPT%"
    exit 1
)

call "%VENV_SCRIPT%"

python3 "%PYTHON_SCRIPT%" %*

call "%MPRC_ROOT%\python\Scripts\deactivate.bat"
