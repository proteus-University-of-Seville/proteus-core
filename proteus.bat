@echo off
setlocal

echo PROTEUS: v1.0.0

@REM Initialize variables
set python_executable=

@REM Check if 'python3.11' is installed
python3.11 --version >nul 2>&1
if not errorlevel 1 (
    set python_executable=python3.11
) else (
    @REM Check if 'python' is installed
    python --version >nul 2>&1
    if not errorlevel 1 (
        set python_executable=python
    ) else (
        @REM Check if 'python3' is installed
        python3 --version >nul 2>&1
        if not errorlevel 1 (
            set python_executable=python3
        )
    )
)

@REM Check if either 'python' or 'python3' is installed
if "%python_executable%"=="" (
    echo PROTEUS: Neither 'python', 'python3', nor 'python3.11' was found on your system.
    echo PROTEUS: Please install Python and try running this script again. Recommended version: 3.11.x
    pause
    exit /b 1
)

echo PROTEUS: %python_executable% is installed on your system.
echo PROTEUS: Installed Python version:
%python_executable% --version || true

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

    %python_executable% -m venv "%venv_dir%"
    
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
for /f "tokens=2 delims= " %%i in ('%python_executable% --version') do set "script_python_version=%%i"
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