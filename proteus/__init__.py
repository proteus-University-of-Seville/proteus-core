# ==========================================================================
# File: __init__.py
# Description: module initialization for the PROTEUS application
# Date: 18/10/2022
# Version: 0.2
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from importlib.metadata import PackageNotFoundError, version as _package_version
from pathlib import Path
import sys

# --------------------------------------------------------------------------
# Application absolute path
# --------------------------------------------------------------------------

# NOTE: this is a workaround for the PyInstaller application. It is needed
#       for the application to work properly when it is packaged as one file.

PROTEUS_APP_PATH = Path(getattr(sys, '_MEIPASS', Path().parent.absolute()))

# --------------------------------------------------------------------------
# PROTEUS version
# --------------------------------------------------------------------------
# Single source of truth: VERSION file at project root. At runtime the
# version is read from the installed package metadata; when running from
# source (launcher scripts) or as a frozen binary, it is read directly
# from the VERSION file.

def _resolve_version() -> str:
    try:
        return f"v{_package_version('PROTEUS')}"
    except PackageNotFoundError:
        pass

    for base_dir in (PROTEUS_APP_PATH, Path(__file__).resolve().parent.parent):
        version_file = base_dir / 'VERSION'
        if version_file.is_file():
            return f"v{version_file.read_text().strip().lstrip('v')}"

    raise RuntimeError("PROTEUS version could not be resolved (VERSION file not found).")

PROTEUS_VERSION = str(_resolve_version())

# --------------------------------------------------------------------------
# Constant declarations for PROTEUS logger
# --------------------------------------------------------------------------

PROTEUS_LOGGER_NAME    = str('proteus')
PROTEUS_LOGGING_FORMAT = str('%(name)s:%(filename)s [%(levelname)s] -> %(message)s')
PROTEUS_MAX_LOG_FILES  = 7

# Temporal file directory

PROTEUS_TEMP_DIR    = PROTEUS_APP_PATH / '.proteus'

# --------------------------------------------------------------------------
# Argument parser
# --------------------------------------------------------------------------
import argparse
parser = argparse.ArgumentParser("Proteus")
parser.add_argument("-p", "--project-path", help="Open the project located in the given path.")

