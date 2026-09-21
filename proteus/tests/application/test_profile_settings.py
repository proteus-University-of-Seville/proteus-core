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
from proteus.model.archetype_repository import ArchetypeRepository


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


# --------------------------------------------------------------------------
# Multi-language archetypes tests
# --------------------------------------------------------------------------
# Profiles may ship one archetype set per language (archetypes/languages.xml,
# same convention already used by the i18n directories). These tests check
# that ProfileSettings resolves the archetypes directory accordingly.


def test_load_profile_settings_multilang_archetypes_default_language():
    """
    Check that the profile's default archetypes language is used when no
    language is requested.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_multilang_archetypes"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path)

    # --------------------
    # Assert
    # --------------------

    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes" / "en_us"
    ), f"Expected: {profile_path / 'archetypes' / 'en_us'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.archetypes_language == "en_us"
    ), f"Expected: en_us, Actual: {profile_settings.archetypes_language}"
    assert list(profile_settings.other_archetypes_language_directories.keys()) == [
        "es_ES"
    ], f"Expected: ['es_ES'], Actual: {list(profile_settings.other_archetypes_language_directories.keys())}"


def test_load_profile_settings_multilang_archetypes_requested_language():
    """
    Check that the requested language's archetypes are used when declared
    and available.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_multilang_archetypes"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path, "es_ES")

    # --------------------
    # Assert
    # --------------------

    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes" / "es_es"
    ), f"Expected: {profile_path / 'archetypes' / 'es_es'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.archetypes_language == "es_es"
    ), f"Expected: es_es, Actual: {profile_settings.archetypes_language}"

    # The archetype content itself must reflect the resolved language
    object_archetypes = ArchetypeRepository.load_object_archetypes(
        profile_settings.archetypes_directory
    )
    paragraph_archetype = object_archetypes["general"]["paragraph"][0]
    assert (
        paragraph_archetype.get_property(":Proteus-name").value == "Párrafo vacío"
    ), f"Expected: 'Párrafo vacío', Actual: {paragraph_archetype.get_property(':Proteus-name').value}"


def test_load_profile_settings_multilang_archetypes_unavailable_language_falls_back():
    """
    Check that the default archetypes language is used when the requested
    language is not declared/available in the profile.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_multilang_archetypes"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path, "fr_FR")

    # --------------------
    # Assert
    # --------------------

    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes" / "en_us"
    ), f"Expected: {profile_path / 'archetypes' / 'en_us'}, Actual: {profile_settings.archetypes_directory}"


def test_load_profile_settings_multilang_archetypes_unresolvable():
    """
    Check that an error is raised when neither the requested language nor
    the profile's default archetypes language can be resolved.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_invalid_multilang_archetypes"

    # --------------------
    # Act
    # --------------------

    with pytest.raises(AssertionError):
        ProfileSettings.load(profile_path, "es_ES")


def test_load_profile_settings_single_language_archetypes_ignore_language():
    """
    Check that profiles without an archetypes/languages.xml file (legacy,
    single-language layout) keep using the archetypes directory as-is,
    regardless of the requested language.
    """
    # --------------------
    # Arrange
    # --------------------

    profile_path = PROTEUS_SAMPLE_PROFILES_PATH / "profile_valid_min"

    # --------------------
    # Act
    # --------------------

    profile_settings = ProfileSettings.load(profile_path, "es_ES")

    # --------------------
    # Assert
    # --------------------

    assert (
        profile_settings.archetypes_directory == profile_path / "archetypes"
    ), f"Expected: {profile_path / 'archetypes'}, Actual: {profile_settings.archetypes_directory}"
    assert (
        profile_settings.archetypes_language is None
    ), f"Expected: None, Actual: {profile_settings.archetypes_language}"