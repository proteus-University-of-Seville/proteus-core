# Display the application name and version
Write-Output "PROTEUS: v1.0.0"

# Initialize variables
$python_executable = $null
$python_args = @()

# Try the py launcher with preferred versions (3.14 -> 3.11)
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in '3.14','3.13','3.12','3.11') {
        & py "-$v" --version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $python_executable = 'py'
            $python_args = @("-$v")
            break
        }
    }
}

# Fall back to generic 'python' / 'python3', but only if version is in 3.11-3.14
if (-not $python_executable) {
    foreach ($cand in 'python','python3') {
        if (-not (Get-Command $cand -ErrorAction SilentlyContinue)) { continue }
        $mm = & $cand -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>$null
        if ($LASTEXITCODE -eq 0 -and $mm -in '3.11','3.12','3.13','3.14') {
            $python_executable = $cand
            break
        }
    }
}

if (-not $python_executable) {
    Write-Output "PROTEUS: No supported Python (3.11-3.14) was found on your system."
    Write-Output "PROTEUS: Please install Python 3.14 (preferred), 3.13, 3.12 or 3.11 and try again."
    Pause
    exit 1
}

# Show selected interpreter and version
$selected_version = (& $python_executable @python_args --version) -split ' ' | Select-Object -Index 1
Write-Output "PROTEUS: Using $python_executable $($python_args -join ' ') (Python $selected_version)"

# Check if the execution policy is set to Unrestricted
Write-Output "PROTEUS: Checking execution policy..."
$execution_policy = Get-ExecutionPolicy -Scope CurrentUser
if ($execution_policy -ne 'Unrestricted') {
    Write-Output "PROTEUS: Execution policy is not set to Unrestricted. This is required to activate the virtual environment."
    Write-Output "PROTEUS: Run the following command in PowerShell as an administrator to set the execution policy to Unrestricted."
    Write-Output "PROTEUS: This might expose your system to security risks, check official documentation for more information."
    Write-Output "PROTEUS: Set-ExecutionPolicy -Scope CurrentUser Unrestricted"
    Pause
    exit 1
}

# Set the script directory and virtual environment directory
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv_dir = Join-Path $script_dir "proteus_env"

# Check for the existence of the virtual environment
Write-Output "PROTEUS: Checking for the existence of virtual environment 'proteus_env'"
if (Test-Path $venv_dir) {
    Write-Output "PROTEUS: Environment 'proteus_env' was found."
} else {
    Write-Output "PROTEUS: Environment 'proteus_env' was not found."
    Write-Output "PROTEUS: Creating a virtual environment using $python_executable..."
    
    & $python_executable @python_args -m venv $venv_dir
    
    if (Test-Path $venv_dir) {
        Write-Output "PROTEUS: Virtual environment created successfully."
    } else {
        Write-Output "PROTEUS: Failed to create the virtual environment."
        Pause
        exit 1
    }
}

# Activate the virtual environment
Write-Output "PROTEUS: Activating the virtual environment..."
& "$venv_dir\Scripts\Activate.ps1"

Write-Output "PROTEUS: Checking the Python version in the virtual environment..."

# Get the Python version from the script environment
$script_python_version = (& $python_executable @python_args --version) -split ' ' | Select-Object -Index 1

# Get the Python version from the virtual environment
$venv_python_version = (& python --version) -split ' ' | Select-Object -Index 1

Write-Output "PROTEUS: Virtual environment Python version: $venv_python_version"

# Check if the versions are different
if ($script_python_version -ne $venv_python_version) {
    Write-Output "PROTEUS: Looks like the Python version in the virtual environment is different from the one chosen by the script."
    Write-Output "PROTEUS: Virtual environment was not activated successfully."
    Write-Output "PROTEUS: Script Python version: $script_python_version"
    Write-Output "PROTEUS: Virtual environment Python version: $venv_python_version"
    Write-Output "PROTEUS: You can try running the app manually by activating the virtual environment and running 'python -m proteus'."
    Pause
    exit 1
}

# Install the required packages
Write-Output "PROTEUS: Installing the required packages..."
& pip install -r "$script_dir\requirements.txt"

# Check for errors while installing the required packages
if ($LASTEXITCODE -ne 0) {
    Write-Output "PROTEUS: Error installing packages. Please check the error message above for details."
    Pause
    exit $LASTEXITCODE
}

# Run the application
Write-Output "PROTEUS: Running the application..."
& python -m proteus

# If there was an error, display the error message and pause
if ($LASTEXITCODE -ne 0) {
    Write-Output "PROTEUS: Error running the application. Please check the error message above for details."
    Pause
    exit $LASTEXITCODE
}