# ==========================================================================
# File: test_profile_settings.py
# Description: pytest file for the PROTEUS profile settings
# Date: 02/04/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.tests import PROTEUS_SAMPLE_PROFILES_PATH
from proteus.application.configuration.profile_settings import ProfileSettings


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------

def test_load_profile_settings_nonexistent_file():
    """
    Check that the profile settings fail when the file does not exist.
    """

    with pytest.raises(AssertionError):
        ProfileSettings.load(Path() / "nonexistent_profile")


# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------
# Dependens on Template and/or Archetype load methods
        
def test_load_profile_settings_min():
    """
    Check that the profile settings are loaded correctly with the minimum
    required data.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_min"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path)

    # --------------------
    # Assert
    # --------------------

    # Check directories
    assert (
        profile_settings.profile_path == profile_path
    ), f"Expected: {profile_path}, Actual: {profile_settings.profile_path}"
    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes"
    ), f"Expected: {profile_path / 'archetypes'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.xslt_directory == profile_path / "templates"
    ), f"Expected: {profile_path / 'templates'}, Actual: {profile_settings.xslt_directory}"
    assert (
        profile_settings.i18n_directory is None
    ), f"Expected: None, Actual: {profile_settings.i18n_directory}"
    assert (
        profile_settings.icons_directory is None
    ), f"Expected: None, Actual: {profile_settings.icons_directory}"
    assert (
        profile_settings.plugins_directory is None
    ), f"Expected: None, Actual: {profile_settings.plugins_directory}"

    # Check preferences
    assert (
        profile_settings.preferred_default_view == "dummy"
    ), f"Expected: dummy, Actual: {profile_settings.preferred_default_view}"

    # Check listed templates number
    assert (
        len(profile_settings.listed_templates) == 1
    ), f"Expected: 1, Actual: {len(profile_settings.listed_templates)}"

def test_load_profile_settings_full():
    """
    Check that the profile settings are loaded correctly with all the
    available data.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_full"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path)

    # --------------------
    # Assert
    # --------------------

    # Check directories
    assert (
        profile_settings.profile_path == profile_path
    ), f"Expected: {profile_path}, Actual: {profile_settings.profile_path}"
    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes"
    ), f"Expected: {profile_path / 'archetypes'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.xslt_directory == profile_path / "templates"
    ), f"Expected: {profile_path / 'templates'}, Actual: {profile_settings.xslt_directory}"
    assert (
        profile_settings.i18n_directory == profile_path / "i18n"
    ), f"Expected: {profile_path / 'i18n'}, Actual: {profile_settings.i18n_directory}"
    assert (
        profile_settings.icons_directory == profile_path / "icons"
    ), f"Expected: {profile_path / 'icons'}, Actual: {profile_settings.icons_directory}"
    assert (
        profile_settings.plugins_directory == profile_path / "plugins"
    ), f"Expected: {profile_path / 'plugins'}, Actual: {profile_settings.plugins_directory}"

    # Check preferences
    assert (
        profile_settings.preferred_default_view == "dummy"
    ), f"Expected: dummy, Actual: {profile_settings.preferred_default_view}"

    # Check listed templates number
    assert (
        len(profile_settings.listed_templates) == 2
    ), f"Expected: 2, Actual: {len(profile_settings.listed_templates)}"


def test_load_profile_optional_dirs_defined_but_not_found():
    """
    Check that the profile settings load correctly when the optional directories
    are defined in the configuration file but they do not exist.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_missing_optional_dirs"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path)

    # --------------------
    # Assert
    # --------------------

    # Check directories
    assert (
        profile_settings.profile_path == profile_path
    ), f"Expected: {profile_path}, Actual: {profile_settings.profile_path}"
    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes"
    ), f"Expected: {profile_path / 'archetypes'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.xslt_directory == profile_path / "templates"
    ), f"Expected: {profile_path / 'templates'}, Actual: {profile_settings.xslt_directory}"
    assert (
        profile_settings.i18n_directory is None
    ), f"Expected: None, Actual: {profile_settings.i18n_directory}"
    assert (
        profile_settings.icons_directory is None
    ), f"Expected: None, Actual: {profile_settings.icons_directory}"
    assert (
        profile_settings.plugins_directory is None
    ), f"Expected: None, Actual: {profile_settings.plugins_directory}"

    # Check preferences
    assert (
        profile_settings.preferred_default_view == "dummy"
    ), f"Expected: dummy, Actual: {profile_settings.preferred_default_view}"

    # Check listed templates number
    assert (
        len(profile_settings.listed_templates) == 1
    ), f"Expected: 1, Actual: {len(profile_settings.listed_templates)}"


def test_load_profile_preferred_view_not_found():
    """
    Check that if the preferred default view is not found in the listed templates,
    the profile settings will pick a one from the list of listed ones.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_invalid_default_view"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path)

    # --------------------
    # Assert
    # --------------------

    # Check preferred default view
    assert (
        profile_settings.preferred_default_view == "dummy"
    ), f"Expected: dummy, Actual: {profile_settings.preferred_default_view}"

    # Check listed templates number
    assert (
        len(profile_settings.listed_templates) == 1
    ), f"Expected: 1, Actual: {len(profile_settings.listed_templates)}"


def test_load_profile_settings_no_valid_templates_found():
    """
    Check that an error is raised when no valid templates are found in the
    templates directory.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_no_valid_templates"

    # --------------------
    # Act
    # --------------------

    with pytest.raises(AssertionError):
        ProfileSettings.load(profile_path)


def test_load_profile_settings_no_valid_archetype_repository():
    """
    Check that an error is raised when the archetype repository is not valid.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_no_valid_archetypes"

    # --------------------
    # Act
    # --------------------

    with pytest.raises(AssertionError):
        ProfileSettings.load(profile_path)