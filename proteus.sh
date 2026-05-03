#!/bin/bash

echo "PROTEUS: v1.0.0"

# Initialize variables
python_executable=

# Try the preferred direct commands first (3.14 -> 3.11)
for cand in python3.14 python3.13 python3.12 python3.11; do
    if command -v "$cand" > /dev/null 2>&1; then
        python_executable="$cand"
        break
    fi
done

# Fall back to generic 'python' / 'python3', but only if version is in 3.11-3.14
if [ -z "$python_executable" ]; then
    for cand in python python3; do
        if command -v "$cand" > /dev/null 2>&1; then
            mm=$("$cand" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
            case "$mm" in
                3.11|3.12|3.13|3.14)
                    python_executable="$cand"
                    break
                    ;;
            esac
        fi
    done
fi

if [ -n "$python_executable" ]; then
    selected_version=$("$python_executable" -c 'import sys; print(sys.version.split()[0])')
    echo "PROTEUS: Using $python_executable (Python $selected_version)"
else
    echo "PROTEUS: No supported Python (3.11-3.14) was found on your system."
    echo "PROTEUS: Please install Python 3.14 (preferred), 3.13, 3.12 or 3.11 and try again."
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
