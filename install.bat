@echo off

:: Creates Python virtual environment and installs required packages.
:: Requires Python 3 with `python` and `pip` to be available in the path.
:: Will also build a standalone executable file.
:: Also set PYTHON_HOME to the appropriate Python base directory.

setlocal EnableDelayedExpansion
call :setESC

:::::::::::::::::::::::::::::::::::::
:: Defaults
:::::::::::::::::::::::::::::::::::::
set REINSTALL=0
set DEBUGMODE=0

:::::::::::::::::::::::::::::::::::::
:: Installation variables
:::::::::::::::::::::::::::::::::::::
set PROGRAM_NAME=csview
set WRAPPER_NAME=%PROGRAM_NAME%.bat
set COMPILED_NAME=%PROGRAM_NAME%.exe
set SCRIPT_NAME=%PROGRAM_NAME%.py
set CURRENT_DIR=%CD%
set CALL_COMMAND=%~f0
:: BASE_DIR will end in a backslash, so don't use separators after it
set BASE_DIR=%~dp0
set CALL_STEM=%~n0
set MYNAME=%CALL_COMMAND%
set MYPATH=%BASE_DIR%
set RESOURCES_DIR_NAME=resources
set RESOURCES_DIR=%BASE_DIR%%RESOURCES_DIR_NAME%
set ICON_NAME=%PROGRAM_NAME%.ico
set ICON=%RESOURCES_DIR%\%ICON_NAME%
set VENV_NAME=venv
set VENV_HOME=%BASE_DIR%%VENV_NAME%
set VENV_SCRIPT=%VENV_HOME%\Scripts\activate.bat
set VENV_DEACTIVATE=%VENV_HOME%\Scripts\deactivate.bat
set DEPS_FILE=requirements.txt
set DEPS_PATH=%BASE_DIR%%DEPS_FILE%
set TEMP_COMPILE_DIR_NAME=build
set TEMP_COMPILE_DIR=%BASE_DIR%%TEMP_COMPILE_DIR_NAME%
set COMPILED_DIR_NAME=dist
set COMPILED_DIR=%BASE_DIR%%COMPILED_DIR_NAME%
set COMPILED_RESULT=%COMPILED_DIR%\%COMPILED_NAME%

set WRAPPER=%BASE_DIR%%WRAPPER_NAME%
set SCRIPT=%BASE_DIR%%SCRIPT_NAME%
set COMPILED=%BASE_DIR%%COMPILED_NAME%

(SET LF=^
%=this line is empty=%
)

:::::::::::::::::::::::::::::::::::::
:: Parse arguments
:::::::::::::::::::::::::::::::::::::
:: Each of these variables contains all the different ways the option can be specified at the command line.
:: These are all in lowercase, but the parser comparison is case insensitive.
set "REINSTALL_ARGS=;-r;--reinstall;-reinstall;/r;/reinstall;"
set "DEBUG_ARGS=;-d;--debug;-debug;/d;/debug;"

set LOCALMATCH=0

:: Just an index for debugging output
set i=0

:: The actual parsing loop
:loop

:: Index for debugging
SET /A i=i+1

IF NOT "%~1"=="" (
    REM Just some debugging output
    REM echo ARG !i!: %~1

    REM This variable keeps track of whether this iteration of the loop has found a match, so we can get positional arguments at the end
    REM set LOCALMATCH=0

    REM This syntax is complex and tricky, but allows you to use a single IF statement to do case-insensitive comparison of the current
    REM option with a whole list of possible ways the user might specify the option. If you don't want this level of flexibility, you
    REM could always do a simpler comparison of the type:
    REM IF "%~1"=="-r" ( ... )
    REM Note that doing it this way will NOT be case-insensitive, and will force the user to specify the option as `-r` instead of also
    REM allowing `--reinstall` or `/r` or the like.
    if "!REINSTALL_ARGS:;%~1%;=!" neq "!REINSTALL_ARGS!" (
        REM This is the REINSTALL flag
        set REINSTALL=1
        REM set LOCALMATCH=1

        REM More debugging output
        @REM echo Reinstall mode enabled

        REM Uncomment if this argument requires a parameter
        REM set PARAMETER=%2
        REM SHIFT
    )
    if "!DEBUG_ARGS:;%~1%;=!" neq "!DEBUG_ARGS!" (
        REM This is the DEBUG flag
        set DEBUGMODE=1
        REM set LOCALMATCH=1

        REM More debugging output
        REM echo Debugging mode enabled
    )

    REM IF NOT "!LOCALMATCH!"=="1" (
    REM     REM Argument was not one of the known options, so it must be a positional argument.
    REM
    REM     REM More debugging output
    REM     echo Found positional argument %1
    REM     set TARGET1=%1
    REM )
    SHIFT
    GOTO :loop
)

:: set ARG1=
:: for /f "usebackq delims==" %%i in (`python -c "import sys ; lcase = sys.argv[1].lower() if len(sys.argv) > 1 else '' ; print(lcase)" %1`) DO (
::     set ARG1=%%i
:: )

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
    exit /b 1
) else (
    call:loginfo "Python script exists: %SCRIPT%"
)

if "%REINSTALL%"=="1" (
    call:reinstall
)

echo.
call:loginfo "Checking existence of Python virtual environment ..."

IF NOT EXIST "%VENV_SCRIPT%" (
    call:loginfo "Python virtual environment does not exist, creating ..."
    python -m venv venv
    IF NOT EXIST "%VENV_SCRIPT%" (
        call:logerr "ERROR: Could not set up Python virtual environment"
        echo.
        exit /b 1
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
    exit /b 1
)

call:loginfo "Python virtual environment is good, continuing ..."
echo.

call:loginfo "Loading Python virtual environment ..."
call "%VENV_SCRIPT%"
call:loginfo "Python virtual environment loaded successfully"
echo.

call:loginfo "Checking existence of required Python packages ..."

:: python -c "import termcolor" 2>NUL
call:check_packages %DEPS_PATH%
if ERRORLEVEL 1 (
    call:logwarn "Required packages are missing, installing required packages ..."
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    :: python -c "import termcolor"
    call:check_packages %DEPS_PATH%
    if ERRORLEVEL 1 (
        echo.
        call:logerr "ERROR: Could not install required Python packages"
        echo.
        exit /b 1
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
if exist %ICON% (
    call:loginfo "Building executable with icon at %COMPILED% ..."
    pyinstaller -i %ICON% -F %SCRIPT_NAME%
    if ERRORLEVEL 1 (
        call:logerr "Building executable with icon threw error %ERRORLEVEL%"
        exit /b 1
    )
) else (
    call:loginfo "Building executable at %COMPILED% ..."
    pyinstaller -F %SCRIPT_NAME%
    if ERRORLEVEL 1 (
        call:logerr "Building executable threw error %ERRORLEVEL%"
        exit /b 1
    )
)
if NOT EXIST %COMPILED_RESULT% (
    call:logerr "Building executable apparently succeeded, but could not find result %COMPILED_RESULT%"
    exit /b 1
)
copy /y %COMPILED_RESULT% %COMPILED%
if NOT EXIST %COMPILED% (
    call:logerr "Could not copy executable to %COMPILED%"
    exit /b 1
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


:trim
SetLocal EnableDelayedExpansion
set Params=%*
for /f "tokens=1*" %%a in ("!Params!") do EndLocal & set %1=%%b
exit /b 0


:lowercase
:: Converts a string to lowercase. Relies on Python.
:: %~1: name of return variable
:: %~2: string to be lowercased
:: ERRORLEVEL: 0 if no errors during conversion, 1 otherwise
SetLocal EnableDelayedExpansion
set RES=%~1
set VAL=%~2
for /f "usebackq delims==" %%i in (`python -c "import sys ; lcase = sys.argv[1].lower() if len(sys.argv) > 1 else '' ; print(lcase)" %VAL%`) DO (
    endlocal
    set %RES%=%%i
)
exit /b 0


:reinstall
:: Removes existing virtual environment, wrapper file, compiled executable, and build directory.
:: ERRORLEVEL: 0 if no errors during removal, 1 otherwise
set REINSTALL_STATUS=0
call:log "REINSTALL: Checking for existing files in '%BASE_DIR%' ..."
call:logdebug "REINSTALL: Checking existence of compiled executable: '%COMPILED%'"
IF EXIST %COMPILED% (
    call:logdebug "REINSTALL: Removing compiled executable '%COMPILED%' ..."
    del /q /f %COMPILED%
    call:logdebug "REINSTALL: Compiled executable removed: '%COMPILED%' ..."
) else (
    call:logdebug "REINSTALL: compiled executable does not exist, no need to remove it"
)

call:logdebug "REINSTALL: Checking existence of executable build directory 1: '%TEMP_COMPILE_DIR%'"
IF EXIST %TEMP_COMPILE_DIR% (
    call:logdebug "REINSTALL: Removing executable build directory 1: '%TEMP_COMPILE_DIR%' ..."
    rd /s/q %TEMP_COMPILE_DIR%
    call:logdebug "REINSTALL: Executable build directory 1 removed: '%TEMP_COMPILE_DIR%' ..."
) else (
    call:logdebug "REINSTALL: Executable build directory 1 does not exist, no need to remove it"
)

call:logdebug "REINSTALL: Checking existence of executable build directory 2: '%COMPILED_DIR%'"
IF EXIST %COMPILED_DIR% (
    call:logdebug "REINSTALL: Removing executable build directory 2: '%COMPILED_DIR%' ..."
    rd /s/q %COMPILED_DIR%
    call:logdebug "REINSTALL: Executable build directory 2 removed: '%COMPILED_DIR%' ..."
) else (
    call:logdebug "REINSTALL: Executable build directory 2 does not exist, no need to remove it"
)

call:logdebug "REINSTALL: Checking existence of wrapper script: '%WRAPPER%'"
IF EXIST %WRAPPER% (
    call:logdebug "REINSTALL: Removing wrapper script '%WRAPPER%' ..."
    del /q /f %WRAPPER%
    call:logdebug "REINSTALL: Wrapper script removed: '%COMPILED%' ..."
) else (
    call:logdebug "REINSTALL: Wrapper script does not exist, no need to remove it"
)

call:logdebug "REINSTALL: Checking existence of Python virtual environment: '%VENV_HOME%'"
IF EXIST %VENV_HOME% (
    call:logdebug "REINSTALL: Removing Python virtual environment '%VENV_HOME%' ..."
    del /q /f %VENV_HOME%
    call:logdebug "REINSTALL: Python virtual environment removed: '%VENV_HOME%' ..."
) else (
    call:logdebug "REINSTALL: Python virtual environment does not exist, no need to remove it"
)

call:logdebug "REINSTALL: Checking for existence of any previous install files ..."
set REINSTALL_FILES_EXIST=0
set FAILMSG=
set ALERT=
IF EXIST %COMPILED% (
    set REINSTALL_FILES_EXIST=1
    set "FAILMSG=compiled executable"
    if defined ALERT (set ALERT=%ALERT%, %FAILMSG%) else (set ALERT=%FAILMSG%)
)
IF EXIST %TEMP_COMPILE_DIR% (
    set REINSTALL_FILES_EXIST=1
    set "FAILMSG=temp build directory"
    if defined ALERT (set ALERT=%ALERT%, %FAILMSG%) else (set ALERT=%FAILMSG%)
)
IF EXIST %COMPILED_DIR% (
    set REINSTALL_FILES_EXIST=1
    set "FAILMSG=build results directory"
    if defined ALERT (set ALERT=%ALERT%, %FAILMSG%) else (set ALERT=%FAILMSG%)
)
IF EXIST %WRAPPER% (
    set REINSTALL_FILES_EXIST=1
    set "FAILMSG=wrapper script"
    if defined ALERT (set ALERT=%ALERT%, %FAILMSG%) else (set ALERT=%FAILMSG%)
)
IF EXIST %VENV_HOME% (
    set REINSTALL_FILES_EXIST=1
    set "FAILMSG=Python virtual environment"
    if defined ALERT (set ALERT=%ALERT%, %FAILMSG%) else (set ALERT=%FAILMSG%)
)
set DEBUG_MSG=Unknown
if defined ALERT (set DEBUG_MSG=%ALERT%)
IF "%REINSTALL_FILES_EXIST%"=="1" (
    call:logerror "REINSTALL: Could not remove all previous install files"
    call:logdebug "REINSTALL: failed to remove: %ALERT%"
    exit /b 1
)
exit /b 0

:check_package
:: Checks to see if a single Python package is installed
:: %~1: name of the package to be checked
:: ERRORLEVEL: 0 if package is installed, 1 if not
set PKG=%~1
python -c "import %PKG%" 2>NUL
IF ERRORLEVEL 1 (
    call:logdebug "check_package: could not import !TRIMMED!, checking if non-module package ..."
    python -c "import subprocess ; available = not(subprocess.run(['pip', 'show', '%PKG%'], capture_output=True, check=True))" 2>NUL
    IF ERRORLEVEL 1 (
        call:logdebug "check_package: %PKG% is not installed"
        exit /b 1
    ) else (
        call:logdebug "check_package: %PKG% is installed according to pip"
    )
) else (
    call:logdebug "check_package: %PKG% found"
)
exit /b 0


:check_packages
:: Checks for required Python packages by trying to import each one
:: %~1: full path to requirements.txt file
:: ERRORLEVEL: 0 if all packages are installed, 1 if not
set PACKAGES=%~1
if [%PACKAGES%]==[""] (
    call:logerr "check_packages: must provide path to a file containing list of packages"
    exit /b 1
)
if not exist %PACKAGES% (
    call:logerr "check_packages: could not find packages file %PACKAGES%"
    exit /b 1
)

set /a c=0
setlocal EnableDelayedExpansion
for /f "tokens=* usebackq" %%i in (%PACKAGES%) do (
    set /a c=c+1
    set LINE=%%i
    call:trim TRIMMED !LINE!
    if [!TRIMMED!]==[] (
        :: trimmed line is empty, ignore it
        echo. >NUL
    ) else (
        :: trimmed lines that begin with # are comments and should be skipped
        set CHAR1=!TRIMMED:~0,1!
        if /i "!CHAR1!"=="#" (
            :: trimmed line is a comment, ignore it
            echo. >NUL
        ) else (
            :: trimmed line is a package name, check if the package exists
            call:logdebug "check_packages: checking package !TRIMMED! ..."
            call:check_package !TRIMMED!
            IF ERRORLEVEL 1 (
                call:logdebug "check_packages: !TRIMMED! not installed"
                exit /b 1
            ) else (
                call:logdebug "check_packages: !TRIMMED! found"
            )
        )
    )
)
endlocal
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
if %DEBUGMODE% equ 1 (
    call :setESC
    echo %ESC%[95m%~1%ESC%[0m
)
exit /b 0

:logerr
call :setESC
echo %ESC%[101;93m%~1%ESC%[0m
exit /b 1


:END
exit /b 0
