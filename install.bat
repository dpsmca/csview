@echo off

REM Creates Python virtual environment and installs required packages for csview.
REM Requires Python 3 with `python` and `pip` to be available in the path.
REM Also set PYTHON_HOME to the appropriate Python base directory.

setlocal EnableDelayedExpansion
call :setESC

set PROGRAM_NAME=csview
set WRAPPER_NAME=%PROGRAM_NAME%.bat
set COMPILED_NAME=%PROGRAM_NAME%.exe
set SCRIPT_NAME=%PROGRAM_NAME%.py
set CURRENT_DIR=%CD%
set CALL_COMMAND=%~f0
@REM BASE_DIR will end in a backslash, so don't use separators after it
set BASE_DIR=%~dp0
set CALL_STEM=%~n0
set MYNAME=%CALL_COMMAND%
set MYPATH=%BASE_DIR%
set VENV_NAME=venv
set VENV_HOME=%BASE_DIR%%VENV_NAME%
set VENV_SCRIPT=%VENV_HOME%\Scripts\activate.bat
set VENV_DEACTIVATE=%VENV_HOME%\Scripts\deactivate.bat
set DEPS_FILE=requirements.txt
set DEPS_PATH=%BASE_DIR%%DEPS_FILE%
set COMPILED_DIR_NAME=dist
set COMPILED_DIR=%BASE_DIR%%COMPILED_DIR_NAME%
set COMPILED_RESULT=%COMPILED_DIR%\%COMPILED_NAME%

set WRAPPER=%BASE_DIR%%WRAPPER_NAME%
set SCRIPT=%BASE_DIR%%SCRIPT_NAME%
set COMPILED=%BASE_DIR%%COMPILED_NAME%

set DEBUGMODE=0

(SET LF=^
%=this line is empty=%
)

set ARG1=
for /f "usebackq delims==" %%i in (`python -c "import sys ; lcase = sys.argv[1].lower() if len(sys.argv) > 1 else '' ; print(lcase)" %1`) DO (
    set ARG1=%%i
)

set DEBUGMODE=0
if [%ARG1%]==[-d] (
    set DEBUGMODE=1
)

if [%ARG1%]==[/d] (
    set DEBUGMODE=1
)

if [%ARG1%]==[-debug] (
    set DEBUGMODE=1
)

if [%ARG1%]==[--debug] (
    set DEBUGMODE=1
)

if [%ARG1%]==[/debug] (
    set DEBUGMODE=1
)

if %DEBUGMODE% EQU 1 (
    echo.
    call:logdebug "============ DEBUG START ============"
    call:logdebug "PROGRAM_NAME=%PROGRAM_NAME%"
    call:logdebug "WRAPPER_NAME=%WRAPPER_NAME%"
    call:logdebug "SCRIPT_NAME=%SCRIPT_NAME%"
    call:logdebug "CALL_COMMAND=%CALL_COMMAND%"
    call:logdebug "CURRENT_DIR=%CURRENT_DIR%"
    call:logdebug "BASE_DIR=%BASE_DIR%"
    call:logdebug "CALL_STEM=%CALL_STEM%"
    call:logdebug "MYNAME=%MYNAME%"
    call:logdebug "MYPATH=%MYPATH%"
    call:logdebug "VENV_NAME=%VENV_NAME%"
    call:logdebug "VENV_HOME=%VENV_HOME%"
    call:logdebug "VENV_SCRIPT=%VENV_SCRIPT%"
    call:logdebug "VENV_DEACTIVATE=%VENV_DEACTIVATE%"
    call:logdebug "DEPS_FILE=%DEPS_FILE%"
    call:logdebug "DEPS_PATH=%DEPS_PATH%"
    call:logdebug "COMPILED_DIR_NAME=%COMPILED_DIR_NAME%"
    call:logdebug "COMPILED_DIR=%COMPILED_DIR%"
    call:logdebug "COMPILED_RESULT=%COMPILED_RESULT%"
    call:logdebug "WRAPPER=%WRAPPER%"
    call:logdebug "SCRIPT=%SCRIPT%"
    call:logdebug "COMPILED=%COMPILED%"
    call:logdebug "============= DEBUG END ============="
    echo.
)

echo.
if NOT [%CURRENT_DIR%]==[%BASE_DIR%] (
  cd "%BASE_DIR%"
)

echo.
call:loginfo "Checking existence of Python script ..."

IF NOT EXIST "%SCRIPT%" (
    call:logerr "ERROR^: could not find Python script: %SCRIPT%"
    echo.
    GOTO :PROBLEM
) else (
    call:loginfo "Python script exists: %SCRIPT%"
)

echo.
call:loginfo "Checking existence of Python virtual environment ..."

IF NOT EXIST "%VENV_SCRIPT%" (
    call:loginfo "Python virtual environment does not exist, creating ..."
    python -m venv venv
    IF NOT EXIST "%VENV_SCRIPT%" (
        call:logerr "ERROR: Could not set up Python virtual environment"
        echo.
        GOTO :PROBLEM
    ) else (
        call:loginfo "Python virtual environment successfully created"
        echo.
    )
) else (
    call:loginfo "Python virtual environment exists"
    echo.
)

IF NOT EXIST "%VENV_SCRIPT%" (
    call:logerr "ERROR: could not find or create Python virtual environment in %VENV_HOME%"
    echo.
    GOTO :PROBLEM
)

call:loginfo "Python virtual environment is good, continuing ..."
echo.

call:loginfo "Loading Python virtual environment ..."
call "%VENV_SCRIPT%"
call:loginfo "Python virtual environment loaded successfully"
echo.

call:loginfo "Checking existence of required Python packages ..."

python -c "import termcolor" 2>NUL
if ERRORLEVEL 1 (
    call:logwarn "Packages not installed, installing required packages ..."
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python -c "import termcolor"
    if ERRORLEVEL 1 (
        echo.
        call:logerr "ERROR: Could not install required Python packages"
        echo.
        goto :PROBLEM
    ) else (
        echo.
        call:loginfo "Successfully installed required Python packages"
        echo.
    )
) else (
    call:loginfo "Required Python packages are already installed"
    echo.
)

call:loginfo "Creating wrapper script at %WRAPPER% ..."

echo @echo off > %WRAPPER%
echo. >> %WRAPPER%
echo set VENV_SCRIPT="%VENV_SCRIPT%" >> %WRAPPER%
echo set VENV_DEACTIVATE="%VENV_DEACTIVATE%" >> %WRAPPER%
echo. >> %WRAPPER%
echo IF NOT EXIST "%VENV_SCRIPT%" ( >> %WRAPPER%
echo   echo ERROR: could not find Python virtual environment at "!VENV_SCRIPT!" >> %WRAPPER%
echo ) else ( >> %WRAPPER%
echo   call "!VENV_SCRIPT!" >> %WRAPPER%
echo. >> %WRAPPER%
echo   python "%SCRIPT%" %%* >> %WRAPPER%
echo. >> %WRAPPER%
echo   call "!VENV_DEACTIVATE!" >> %WRAPPER%
echo ) >> %WRAPPER%
echo. >> %WRAPPER%

call:loginfo "Wrapper script created: %WRAPPER%"

echo.
call:loginfo "Building executable at %COMPILED% ..."
pyinstaller -F %SCRIPT_NAME%
if ERRORLEVEL 1 (
    call:logerr "Building executable threw error %ERRORLEVEL%"
    goto :PROBLEM
)
if NOT EXIST %COMPILED_RESULT% (
    call:logerr "Building executable apparently succeeded, but could not find result %COMPILED_RESULT%"
    goto :PROBLEM
)
copy /y %COMPILED_RESULT% %COMPILED%
if NOT EXIST %COMPILED% (
    call:logerr "Could not copy executable to %COMPILED%"
    goto :PROBLEM
)
call:loginfo "Executable created: %COMPILED%"

call:logsuccess "%PROGRAM_NAME% has been set up successfully"
call:logsuccess "Run with python command: python %SCRIPT%"
call:logsuccess "Or with wrapper script: %WRAPPER%"
call:logsuccess "Or with executable file: %COMPILED%"

GOTO :END

:setESC
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set ESC=%%b
  exit /B 0
)
exit /b 0

:loginfo
call :setESC
echo %ESC%[96m%~1%ESC%[0m
exit /b 0

:logsuccess
call :setESC
@REM echo %ESC%[92m%~1%ESC%[0m
echo %ESC%[42m%ESC%[97m%~1%ESC%[0m
exit /b 0

:logwarn
call :setESC
echo %ESC%[93m%~1%ESC%[0m
exit /b 0

:logdebug
call :setESC
echo %ESC%[95m%~1%ESC%[0m
exit /b 0

:logerr
call :setESC
echo %ESC%[101;93m%~1%ESC%[0m
exit /b 1


:END
exit /b 0
