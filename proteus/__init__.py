# ==========================================================================
# File: __init__.py
# Description: module initialization for the PROTEUS application
# Date: 18/10/2022
# Version: 0.2
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# PROTEUS version
# --------------------------------------------------------------------------
PROTEUS_VERSION = str('v1.0.0')

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path
import sys

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

# Temporal file directory

PROTEUS_TEMP_DIR    = PROTEUS_APP_PATH / '.proteus'

# --------------------------------------------------------------------------
# Argument parser
# --------------------------------------------------------------------------
import argparse
parser = argparse.ArgumentParser("Proteus")
parser.add_argument("-p", "--project-path", help="Open the project located in the given path.")

