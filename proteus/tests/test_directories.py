# ==========================================================================
# File: test_directories.py
# Description: pytest file for the PROTEUS application directories
# Date: 10/10/2022
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------
from proteus.application.configuration.config import Config
# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_application_directories():
    """
    It tests that essential PROTEUS directories exist.
    """
    app : Config = Config()
    assert app.app_settings.resources_directory.is_dir()
    assert app.app_settings.i18n_directory.is_dir()
    assert app.app_settings.profiles_directory.is_dir()
    # Icons no longer live at the app level — they live inside each theme.
    # Verify the canonical baseline (light theme) is present and complete.
    light_icons = app.app_settings.resources_directory / "themes" / "light" / "icons"
    assert light_icons.is_dir(), f"Baseline theme icons missing at {light_icons}"
    assert (light_icons / "icons.xml").is_file(), \
        f"Baseline theme icons.xml missing at {light_icons / 'icons.xml'}"

    assert app.profile_settings.archetypes_directory.is_dir()
    assert app.profile_settings.xslt_directory.is_dir()
