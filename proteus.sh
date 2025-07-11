#!/bin/bash

echo "PROTEUS: v1.0.0"

# Initialize variables
python_executable=

# Check if either 'python' or 'python3' is installed
if command -v python3.11 > /dev/null 2>&1; then
    python_executable=python3.11
elif command -v python > /dev/null 2>&1; then
    python_executable=python
elif command -v python3 > /dev/null 2>&1; then
    python_executable=python3
fi

if [ -n "$python_executable" ]; then
    echo "PROTEUS: $python_executable is installed on your system."
    echo "PROTEUS: Installed Python version:"
    $python_executable --version || true
else
    echo "PROTEUS: Neither 'python', 'python3', nor 'python3.11' was found on your system."
    echo "PROTEUS: Please install Python and try running this script again. Recommended version: 3.11.x"
    exit 1
fi

script_dir="$(dirname "$0")"
venv_dir="$script_dir/proteus_env"

echo "PROTEUS: Checking for the existence of virtual environment 'proteus_env'"
if [ -d "$venv_dir" ]; then
    echo "PROTEUS: Environment 'proteus_env' was found."
else
    echo "PROTEUS: Environment 'proteus_env' was not found."
    echo "PROTEUS: Creating a virtual environment using $python_executable..."

    $python_executable -m venv "$venv_dir"
    
    if [ -d "$venv_dir" ]; then
        echo "PROTEUS: Virtual environment created successfully."
    else
        echo "PROTEUS: Failed to create the virtual environment."

        # If failed to create the venv, show the error message and exit
        exit 1
    fi
fi

echo "PROTEUS: Activating the virtual environment..."
source "$venv_dir/bin/activate"


# Check if the virtual environment is activated
if [ $? -ne 0 ]; then
    echo "PROTEUS: Failed to activate the virtual environment. Check if python venv package is installed."
    # Delete proteus_env if it exists
    if [ -d "$venv_dir" ]; then
        rm -rf "$venv_dir"
    fi
    exit 1
fi

echo "PROTEUS: Virtual environment Python version:"
python --version || true

echo "PROTEUS: Installing the required packages..."
pip install -r "$script_dir/requirements.txt"

# Run the application in the background so the console can be closed
echo "PROTEUS: Running the application..."
python -m proteus &
