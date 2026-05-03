# ==========================================================================
# File: test_app_settings.py
# Description: pytest file for the PROTEUS app settings
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

from proteus import PROTEUS_APP_PATH
from proteus.tests import PROTEUS_SAMPLE_INIT_FILES_PATH
from proteus.application.configuration.app_settings import AppSettings, CONFIG_FILE

# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------

# Init file is read from the current working directory (CWD) using Path.cwd(),
# To avoid copying the init file to the test working directory, tests must
# mock Path.cwd() to return correct path to the sample data folder for each test.


def test_load_app_settings_min(mocker):
    """
    Check that minimal app settings are loaded correctly.
    """

    # --------------------
    # Arrange
    # --------------------

    app_settings_path = PROTEUS_SAMPLE_INIT_FILES_PATH / "init_min"

    mocker.patch("pathlib.Path.cwd", return_value=app_settings_path)

    # --------------------
    # Act
    # --------------------

    app_settings = AppSettings.load(PROTEUS_APP_PATH)

    # --------------------
    # Assert
    # --------------------

    # Check directories
    assert (
        app_settings.profiles_directory == PROTEUS_APP_PATH / "profiles"
    ), f"Expected profiles directory '{PROTEUS_APP_PATH / 'profiles'}, but got '{app_settings.profiles_directory}'"
    assert (
        app_settings.resources_directory == PROTEUS_APP_PATH / "resources"
    ), f"Expected templates directory '{PROTEUS_APP_PATH / 'resources'}, but got '{app_settings.resources_directory}'"
    assert (
        app_settings.i18n_directory == app_settings.resources_directory / "i18n"
    ), f"Expected languages directory '{app_settings.resources_directory / 'i18n'}, but got '{app_settings.i18n_directory}'"
    # icons_directory has been removed from AppSettings — icons live under
    # themes/{theme}/icons/ now and are resolved via the Themes singleton.

    # Check user settings
    assert (
        app_settings.language == "en_US"
    ), f"Expected language 'en_US', but got '{app_settings.language}'"
    # init_min/proteus.ini doesn't declare a `theme` key; the loader must
    # fall back to DEFAULT_THEME ("light"). This catches regressions where
    # the missing-key fallback gets dropped or set to None.
    assert (
        app_settings.theme == "light"
    ), f"Expected theme 'light' (default), but got '{app_settings.theme}'"
    assert (
        app_settings.default_view == "dummy_view"
    ), f"Expected default view 'dummy_view', but got '{app_settings.default_view}'"
    assert (
        app_settings.selected_profile == "dummy_profile"
    ), f"Expected default profile 'dummy_profile', but got '{app_settings.selected_profile}'"
    assert (
        app_settings.using_default_profile == True
    ), f"Expected using default profile 'True', but got '{app_settings.using_default_profile}'"
    assert (
        app_settings.custom_profile_path == None
    ), f"Expected custom profile path 'None', but got '{app_settings.custom_profile_path}'"


def test_load_settings_custom_profile_none_path(mocker):
    """
    Check that the settings are handled correctly if the using default profile is False
    and custom profile path is None.
    """

    # --------------------
    # Arrange
    # --------------------

    app_settings_path = PROTEUS_SAMPLE_INIT_FILES_PATH / "init_custom_profile_none_path"

    mocker.patch("pathlib.Path.cwd", return_value=app_settings_path)

    # --------------------
    # Act
    # --------------------

    app_settings = AppSettings.load(PROTEUS_APP_PATH)

    # --------------------
    # Assert
    # --------------------

    # Check relevant settings according to the tests, other settings are checked in other tests

    # Check using default profile changed to True
    assert (
        app_settings.using_default_profile == True
    ), f"Expected using default profile 'True', but got '{app_settings.using_default_profile}'"
    assert (
        app_settings.custom_profile_path == None
    ), f"Expected custom profile path 'None', but got '{app_settings.custom_profile_path}'"


def test_load_settings_custom_profile_nonexisting_path(mocker):
    """
    Check that the settings are handled correctly if the using default profile is False
    and custom profile path is a non-existing path.
    """

    # --------------------
    # Arrange
    # --------------------

    app_settings_path = (
        PROTEUS_SAMPLE_INIT_FILES_PATH / "init_custom_profile_nonexisting_path"
    )

    mocker.patch("pathlib.Path.cwd", return_value=app_settings_path)

    # --------------------
    # Act
    # --------------------

    app_settings = AppSettings.load(PROTEUS_APP_PATH)

    # --------------------
    # Assert
    # --------------------

    # Check relevant settings according to the tests, other settings are checked in other tests

    # Check using default profile changed to True
    assert (
        app_settings.using_default_profile == True
    ), f"Expected using default profile 'True', but got '{app_settings.using_default_profile}'"
    assert (
        app_settings.custom_profile_path.as_posix() == "/path/to/nowhere"
    ), f"Expected custom profile path '/path/to/nowhere', but got '{app_settings.custom_profile_path}'"


def test_load_settings_copy_file_to_cwd(mocker):
    """
    Check that generic proteus.ini file is copied to the current working directory if
    not found and then loaded.
    """

    # --------------------
    # Arrange
    # --------------------

    app_settings_path = PROTEUS_SAMPLE_INIT_FILES_PATH

    mocker.patch("pathlib.Path.cwd", return_value=app_settings_path)

    # Check that the file does not exist before loading
    if (app_settings_path / CONFIG_FILE).exists():
        (app_settings_path / CONFIG_FILE).unlink()

    # --------------------
    # Act
    # --------------------

    app_settings = AppSettings.load(PROTEUS_APP_PATH)

    # --------------------
    # Assert
    # --------------------

    # Check the file was copied to the current working directory
    assert (
        app_settings_path / CONFIG_FILE
    ).exists(), (
        f"Expected file '{app_settings_path / CONFIG_FILE}' to exist, but it does not"
    )

    assert (
        app_settings.settings_file_path == app_settings_path / CONFIG_FILE
    ), f"Expected settings file path '{app_settings_path / CONFIG_FILE}', but got '{app_settings.settings_file_path}'"

    # --------------------
    # Clean up
    # --------------------

    # Remove the copied file
    if (app_settings_path / CONFIG_FILE).exists():
        (app_settings_path / CONFIG_FILE).unlink()


@pytest.mark.parametrize(
    "language, default_view, selected_profile, using_default_profile, custom_profile_path, theme, expected_using_default_profile, expected_custom_profile_path",
    [
        (None, None, None, None, None, None, None, None),
        ("es_ES", None, None, None, None, None, None, None),
        (None, "another_view", None, None, None, None, None, None),
        (None, None, "another_profile", None, None, None, None, None),
        (None, None, None, False, None, None, True, None),  # Invalid path
        (
            None,
            None,
            None,
            False,
            Path("/path/to/nowhere"),
            None,
            True,
            Path("/path/to/nowhere"),
        ),  # Invalid path
        (
            None,
            None,
            None,
            False,
            Path(),
            None,
            False,
            Path(),
        ),  # NOTE: Profile validation is not performed in app settings so this is valid
        (None, None, None, None, None, "dark", None, None),  # theme override
    ],
)
def test_app_settings_clone(
    language: str,
    default_view: str,
    selected_profile: str,
    using_default_profile: bool,
    custom_profile_path: Path,
    theme: str,
    expected_using_default_profile: bool,
    expected_custom_profile_path: Path,
):
    """
    Test the clone method of the AppSettings class.
    """
    # --------------------
    # Arrange
    # --------------------

    app_settings = AppSettings.load(PROTEUS_APP_PATH)

    # --------------------
    # Act
    # --------------------

    cloned_settings = app_settings.clone(
        language=language,
        default_view=default_view,
        selected_profile=selected_profile,
        using_default_profile=using_default_profile,
        custom_profile_path=custom_profile_path,
        theme=theme,
    )

    # --------------------
    # Assert
    # --------------------
    # Assertions are made depending if the parameter is None or not

    if language is None:
        assert (
            cloned_settings.language == app_settings.language
        ), f"Expected language '{app_settings.language}', but got '{cloned_settings.language}'"
    else:
        assert (
            cloned_settings.language == language
        ), f"Expected language '{language}', but got '{cloned_settings.language}'"

    if default_view is None:
        assert (
            cloned_settings.default_view == app_settings.default_view
        ), f"Expected default view '{app_settings.default_view}', but got '{cloned_settings.default_view}'"
    else:
        assert (
            cloned_settings.default_view == default_view
        ), f"Expected default view '{default_view}', but got '{cloned_settings.default_view}'"

    if selected_profile is None:
        assert (
            cloned_settings.selected_profile == app_settings.selected_profile
        ), f"Expected selected profile '{app_settings.selected_profile}', but got '{cloned_settings.selected_profile}'"
    else:
        assert (
            cloned_settings.selected_profile == selected_profile
        ), f"Expected selected profile '{selected_profile}', but got '{cloned_settings.selected_profile}'"

    # Compare using the expected values. They might change after clone due to validation in clone method
    if expected_custom_profile_path is None:
        assert (
            cloned_settings.custom_profile_path == app_settings.custom_profile_path
        ), f"Expected custom profile path '{app_settings.custom_profile_path}', but got '{cloned_settings.custom_profile_path}'"
    else:
        assert (
            cloned_settings.using_default_profile == expected_using_default_profile
        ), f"Expected using default profile '{expected_using_default_profile}', but got '{cloned_settings.using_default_profile}'"

    if expected_custom_profile_path is None:
        assert (
            cloned_settings.custom_profile_path == app_settings.custom_profile_path
        ), f"Expected custom profile path '{app_settings.custom_profile_path}', but got '{cloned_settings.custom_profile_path}'"
    else:
        assert (
            cloned_settings.custom_profile_path == expected_custom_profile_path
        ), f"Expected custom profile path '{expected_custom_profile_path}', but got '{cloned_settings.custom_profile_path}'"

    # Theme: when None is passed, clone must preserve the original value;
    # when a string is passed, clone must adopt it.
    if theme is None:
        assert (
            cloned_settings.theme == app_settings.theme
        ), f"Expected theme '{app_settings.theme}' (preserved), but got '{cloned_settings.theme}'"
    else:
        assert (
            cloned_settings.theme == theme
        ), f"Expected theme '{theme}' (override), but got '{cloned_settings.theme}'"
