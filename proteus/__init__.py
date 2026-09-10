# ==========================================================================
# File: __init__.py
# Description: module initialization for the PROTEUS application
# Date: 10/09/2026
# Version: 1.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# PROTEUS version
# --------------------------------------------------------------------------
PROTEUS_VERSION = str('1.1.0')
PROTEUS_VERSION_YEAR = str('2026')

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import sys
import argparse
from pathlib import Path

# --------------------------------------------------------------------------
# Application absolute path
# --------------------------------------------------------------------------

# NOTE: this is a workaround for the PyInstaller application. It is needed
#       for the application to work properly when it is packaged as one file.

PROTEUS_APP_PATH = Path(getattr(sys, '_MEIPASS', Path().parent.absolute()))

# --------------------------------------------------------------------------
# Constant declarations for PROTEUS logger
# --------------------------------------------------------------------------

PROTEUS_LOGGER_NAME    = str('proteus')
PROTEUS_LOGGING_FORMAT = str('%(name)s:%(filename)s [%(levelname)s] -> %(message)s')
PROTEUS_MAX_LOG_FILES  = 7

# --------------------------------------------------------------------------
# Temporal file directory
# --------------------------------------------------------------------------

PROTEUS_TEMP_DIR    = PROTEUS_APP_PATH / '.proteus'

# --------------------------------------------------------------------------
# Argument parser
# --------------------------------------------------------------------------

parser = argparse.ArgumentParser("Proteus")
parser.add_argument("-p", "--project-path", help="Open the project located in the given path.")
