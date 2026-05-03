@echo off
setlocal enabledelayedexpansion

echo PROTEUS: v1.0.0

@REM Initialize variables
set python_executable=
set python_args=

@REM Try the py launcher with preferred versions (3.14 -> 3.11)
for %%v in (3.14 3.13 3.12 3.11) do (
    if not defined python_executable (
        py -%%v --version >nul 2>&1
        if not errorlevel 1 (
            set python_executable=py
            set python_args=-%%v
        )
    )
)

@REM Fall back to generic 'python' / 'python3', but only if version is in 3.11-3.14
if not defined python_executable (
    for %%c in (python python3) do (
        if not defined python_executable (
            for /f "tokens=2 delims= " %%V in ('%%c --version 2^>nul') do (
                for /f "tokens=1,2 delims=." %%a in ("%%V") do (
                    if "%%a"=="3" (
                        if "%%b"=="11" set python_executable=%%c
                        if "%%b"=="12" set python_executable=%%c
                        if "%%b"=="13" set python_executable=%%c
                        if "%%b"=="14" set python_executable=%%c
                    )
                )
            )
        )
    )
)

if not defined python_executable (
    echo PROTEUS: No supported Python ^(3.11-3.14^) was found on your system.
    echo PROTEUS: Please install Python 3.14 ^(preferred^), 3.13, 3.12 or 3.11 and try again.
    pause
    exit /b 1
)

@REM Show selected interpreter and version
for /f "tokens=2 delims= " %%i in ('%python_executable% %python_args% --version') do set "selected_version=%%i"
echo PROTEUS: Using %python_executable% %python_args% ^(Python %selected_version%^)

@REM Check execution policy is set to Unrestricted, if not tell the user and exit
echo PROTEUS: Checking execution policy...
powershell -Command "if ((Get-ExecutionPolicy -Scope CurrentUser) -ne 'Unrestricted') { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo PROTEUS: Execution policy is not set to Unrestricted. This is required to activate the virtual environment.
    echo PROTEUS: You can check the current execution policy by running the following command in PowerShell: Get-ExecutionPolicy -Scope CurrentUser
    echo PROTEUS: This might expose your system to security risks, check official documentation for more information https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.3 .
    echo PROTEUS: Run the following command in PowerShell as an administrator to set the execution policy to Unrestricted.
    echo PROTEUS: Set-ExecutionPolicy -Scope CurrentUser Unrestricted
    echo PROTEUS: If you have already set the execution policy to Unrestricted, this might be caused due to powershell not being in the PATH, use the PowerShell script "proteus.ps1" to run the application.
    pause
    exit /b 1
)

set "script_dir=%~dp0"
set "venv_dir=%script_dir%proteus_env"

echo PROTEUS: Checking for the existence of virtual environment "proteus_env"
if exist "%venv_dir%" (
    echo PROTEUS: Environment "proteus_env" was found.
) else (
    echo PROTEUS: Environment "proteus_env" was not found.
    echo PROTEUS: Creating a virtual environment using %python_executable%...

    %python_executable% %python_args% -m venv "%venv_dir%"
    
    if exist "%venv_dir%" (
        echo PROTEUS: Virtual environment created successfully.
    ) else (
        echo PROTEUS: Failed to create the virtual environment.

        @REM If failed to create the venv, show the error message and pause
        pause
        exit /b 1
    )
)

echo PROTEUS: Activating the virtual environment...
call "%venv_dir%\Scripts\activate.bat"

echo PROTEUS: Checking the Python version in the virtual environment...
for /f "tokens=2 delims= " %%i in ('%python_executable% %python_args% --version') do set "script_python_version=%%i"
for /f "tokens=2 delims= " %%i in ('python --version') do set "venv_python_version=%%i"

echo PROTEUS: Virtual environment Python version: %venv_python_version%

if not "%script_python_version%"=="%venv_python_version%" (
    echo PROTEUS: Looks like the Python version in the virtual environment is different from the one chosen by the script.
    echo PROTEUS: Virutal environment was not activated successfully.
    echo PROTEUS: Script Python version: %script_python_version%
    echo PROTEUS: Virtual environment Python version: %venv_python_version%
    echo PROTEUS: Try using the PowerShell script "proteus.ps1" in order to run the application.
    pause
    exit /b 1
)

echo PROTEUS: Installing the required packages...
pip install -r "%script_dir%requirements.txt"

@REM Check for errors while installing the required packages
if %errorlevel% NEQ 0 (
    echo PROTEUS: Error installing packages. Please check the error message above for details.
    pause
    exit /b %errorlevel%
)

@REM Run the application in the background so the console can be closed
echo PROTEUS: Running the application...
call python -m proteus

if errorlevel 1 (
    echo PROTEUS: Error running the application. Please check the error message above for details.
    pause
    exit /b 1
)

endlocal