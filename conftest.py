# ==========================================================================
# File: confest.py
# Description: pytest root configuration for PROTEUS application tests
# Date: 01/05/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import os


def pytest_addoption(parser):
    """
    Add command-line options for pytest.
    """
    parser.addoption(
        "--no-gui",
        action="store_true",
        default=False,
        help="Run Qt tests with QT_QPA_PLATFORM=offscreen.",
    )


def pytest_configure(config):
    if config.getoption("--no-gui"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
