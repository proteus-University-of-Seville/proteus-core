# ==========================================================================
# File: test_config_dialog.py
# Description: pytest file for the PROTEUS pyqt config fialog
# Date: 29/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtWidgets import QMessageBox

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

import proteus
from proteus.application.configuration.config import Config
from proteus.application.configuration.app_settings import AppSettings
from proteus.views.components.main_window import MainWindow
from proteus.views.components.dialogs.settings_dialog import SettingsDialog
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.tests.end2end.fixtures import app, get_dialog

# --------------------------------------------------------------------------
# Fixtures / Helper functions
# --------------------------------------------------------------------------


@pytest.fixture(scope="function")
def app_settings():
    """
    Return app settings and restore them after the test. Restoration is done
    by saving the settings (not app_settings_copy).
    """
    # Config singleton
    config = Config()

    # Return settings
    yield config.app_settings

    # Restore settings
    config.app_settings.save()


# # --------------------------------------------------------------------------
# # End to end "config dialog" tests
# # --------------------------------------------------------------------------


def test_config_dialog_open(app, app_settings: AppSettings):
    """
    Opens the config dialog and checks if the settings are correctly
    loaded.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Check if dialog was created correctly
    assert isinstance(
        dialog, SettingsDialog
    ), f"Dialog is not an instance of SettingsDialog but {type(dialog)}"

    # Check language setting was correctly set in the combo box
    current_language = dialog.language_combo.currentData()

    assert (
        current_language == app_settings.language
    ), f"Language setting is {current_language} but should be {app_settings.language}"

    # Check default view setting was correctly set in the combo box
    current_default_view = dialog.default_view_combo.currentData()

    assert (
        current_default_view == app_settings.default_view
    ), f"Default view setting is {current_default_view} but should be {app_settings.default_view}"

    # Check selected profile setting was correctly set in the combo box
    current_selected_profile = dialog.profile_combo.currentData()

    assert (
        current_selected_profile == app_settings.selected_profile
    ), f"Selected profile setting is {current_selected_profile} but should be {app_settings.selected_profile}"

    # Check using_default_profile setting was correctly set in the checkbox
    use_custom_profile_checkbox = dialog.use_custom_profile_checkbox.isChecked()

    assert use_custom_profile_checkbox == (
        not app_settings.using_default_profile
    ), f"Use custom profile setting is {use_custom_profile_checkbox} but should be {not app_settings.using_default_profile}"

    # Check custom_profile_path setting was correctly set in directory edit and checkbox
    current_custom_profile_path = dialog.custom_profile_edit.directory()

    custom_profile_path = (
        app_settings.custom_profile_path.as_posix()
        if app_settings.custom_profile_path
        else ""
    )

    assert (
        current_custom_profile_path == custom_profile_path
    ), f"Custom profile path setting is {current_custom_profile_path} but should be {app_settings.custom_profile_path}"


@pytest.mark.skip("Temporary disabled because test data changed")
def test_config_dialog_change_settings(app, app_settings: AppSettings):
    """
    Opens the config dialog and changes the settings. Then checks if
    the settings were correctly changed (file and dialog).

    app_settings fixture is used to restore the settings file to its
    original state. It also works when the test fails.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Change settings
    new_language = "es_ES"
    new_default_view = "figures"

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # Change language
    new_lang_index = dialog.language_combo.findData(new_language)
    dialog.language_combo.setCurrentIndex(new_lang_index)

    # Change default view
    new_default_view_index = dialog.default_view_combo.findData(new_default_view)

    current_description = dialog.view_description_label.text()
    dialog.default_view_combo.setCurrentIndex(new_default_view_index)

    # Save settings
    warning_dialog: MessageBox = get_dialog(dialog.accept_button.click)
    warning_dialog.button(QMessageBox.StandardButton.Ok).click()
    dialog.deleteLater()
    warning_dialog.deleteLater()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # ---------------------
    # Check dialog
    # ---------------------

    # Open again the config dialog and check if the settings were correctly changed
    second_dialog: SettingsDialog = get_dialog(settings_button.click)

    # Check language setting was correctly set in the combo box
    current_language = second_dialog.language_combo.currentData()

    assert (
        current_language == new_language
    ), f"Language setting is '{current_language}' but should be '{new_language}'"

    # Check default view setting was correctly set in the combo box
    current_default_view = second_dialog.default_view_combo.currentData()

    assert (
        current_default_view == new_default_view
    ), f"Default view setting is '{current_default_view}' but should be '{new_default_view}'"

    # Check description was correctly changed
    new_description = second_dialog.view_description_label.text()
    assert (
        new_description != current_description
    ), f"Description was not correctly changed. It is '{new_description}' but should be different from '{current_description}'"

    # ---------------------
    # Check file
    # ---------------------

    # Read settings file and check if the setting were correctly changed
    # Creates config parser using Config to make code easier
    new_app_settings = AppSettings.load(proteus.PROTEUS_APP_PATH)

    app_settings_copy = Config().app_settings_copy

    # Check language setting
    assert (
        new_app_settings.language == new_language == app_settings_copy.language
    ), f"Language settings was not correctly saved. It is {new_app_settings.language} but should be {new_language} | app: {app_settings_copy.language}"

    # Check default view setting
    assert (
        new_app_settings.default_view
        == new_default_view
        == app_settings_copy.default_view
    ), f"Default view settings was not correctly saved. It is {new_app_settings.default_view} but should be {new_default_view} | app: {app_settings_copy.default_view}"


@pytest.mark.skip("Temporary disabled because there is only one profile")
def test_config_dialog_change_profile(app, app_settings: AppSettings):
    """
    Opens the config dialog and changes the profile settings. Then checks if
    the settings were correctly changed (file and dialog).

    app_settings fixture is used to restore the settings file to its
    original state. It also works when the test fails.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Change settings
    new_profile = "madeja_ir_spanish"

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # Change profile
    current_description = dialog.profile_description_label.text()
    new_profile_index = dialog.profile_combo.findData(new_profile)
    dialog.profile_combo.setCurrentIndex(new_profile_index)

    # Save settings
    warning_dialog: MessageBox = get_dialog(dialog.accept_button.click)
    warning_dialog.button(QMessageBox.StandardButton.Ok).click()
    dialog.deleteLater()
    warning_dialog.deleteLater()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # ---------------------
    # Check dialog
    # ---------------------

    # Open again the config dialog and check if the settings were correctly changed
    second_dialog: SettingsDialog = get_dialog(settings_button.click)

    # Check selected profile setting was correctly set in the combo box
    current_selected_profile = second_dialog.profile_combo.currentData()

    assert (
        current_selected_profile == new_profile
    ), f"Selected profile setting is '{current_selected_profile}' but should be '{new_profile}'"

    # Check description was correctly changed
    new_description = second_dialog.profile_description_label.text()
    assert (
        new_description != current_description
    ), f"Description was not correctly changed. It is '{new_description}' but should be different from '{current_description}'"

    # Check using_custom_profile setting is False
    use_custom_profile_checkbox = second_dialog.use_custom_profile_checkbox.isChecked()

    assert (
        use_custom_profile_checkbox is False
    ), "Use custom profile setting is '{use_custom_profile_checkbox}' but should be 'False'"

    # Check custom_profile_path is disabled
    assert (
        second_dialog.custom_profile_edit.isEnabled() is False
    ), "Custom profile path is enabled but should be disabled"

    # ---------------------
    # Check file
    # ---------------------

    # Read settings file and check if the setting were correctly changed
    # Creates config parser using Config to make code easier
    new_app_settings = AppSettings.load(proteus.PROTEUS_APP_PATH)

    app_settings_copy = Config().app_settings_copy

    # Check selected profile setting
    assert (
        new_app_settings.selected_profile
        == new_profile
        == app_settings_copy.selected_profile
    ), f"Selected profile settings was not correctly saved. It is '{new_app_settings.selected_profile}' but should be '{new_profile}' | app: {app_settings_copy.selected_profile}"

    # Check using_custom_profile setting
    assert (
        new_app_settings.using_default_profile
        is True
        == app_settings_copy.using_default_profile
    ), f"Using default profile settings was not correctly saved. It is '{new_app_settings.using_default_profile}' but should be 'True' | app: {app_settings_copy.using_default_profile}"


def test_config_dialog_change_custom_profile(app, app_settings: AppSettings):
    """
    Opens the config dialog and changes the custom profile settings. Then checks if
    the settings were correctly changed (file and dialog).

    app_settings fixture is used to restore the settings file to its
    original state. It also works when the test fails.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Change settings
    new_custom_profile_path = (
        Config().app_settings.profiles_directory / "basic"
    )

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    was_enabled_custom_profile_path = dialog.custom_profile_edit.isEnabled()
    was_enabled_profile_combo = dialog.profile_combo.isEnabled()

    # Change custom profile path
    dialog.use_custom_profile_checkbox.setChecked(True)
    dialog.custom_profile_edit.setDirectory(new_custom_profile_path.as_posix())

    is_enabled_custom_profile_path = dialog.custom_profile_edit.isEnabled()
    is_enabled_profile_combo = dialog.profile_combo.isEnabled()

    # Save settings
    warning_dialog: MessageBox = get_dialog(dialog.accept_button.click)
    warning_dialog.button(QMessageBox.StandardButton.Ok).click()
    dialog.deleteLater()
    warning_dialog.deleteLater()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    assert (
        was_enabled_custom_profile_path is False
    ), "Custom profile path was enabled before checking the checkbox but should be disabled"

    assert (
        was_enabled_profile_combo is True
    ), "Profile combo was disabled before checking the checkbox but should be enabled"

    assert (
        is_enabled_custom_profile_path is True
    ), "Custom profile path is disabled but should be enabled after checking the checkbox"

    assert (
        is_enabled_profile_combo is False
    ), "Profile combo is enabled but should be disabled after checking the checkbox"

    # ---------------------
    # Check dialog
    # ---------------------

    # Open again the config dialog and check if the settings were correctly changed
    second_dialog: SettingsDialog = get_dialog(settings_button.click)

    # Check combo is disabled and custom profile path is enabled
    assert (
        second_dialog.profile_combo.isEnabled() is False
    ), "Profile combo is enabled but should be disabled"

    assert (
        second_dialog.custom_profile_edit.isEnabled() is True
    ), "Custom profile path is disabled but should be enabled"

    # Check custom_profile_path setting was correctly set in directory edit and checkbox
    current_custom_profile_path = second_dialog.custom_profile_edit.directory()

    assert (
        current_custom_profile_path == new_custom_profile_path.as_posix()
    ), f"Custom profile path setting is '{current_custom_profile_path}' but should be '{new_custom_profile_path}'"

    # Check using_custom_profile setting is True
    use_custom_profile_checkbox = second_dialog.use_custom_profile_checkbox.isChecked()

    assert (
        use_custom_profile_checkbox is True
    ), f"Use custom profile setting is '{use_custom_profile_checkbox}' but should be 'True'"

    # ---------------------
    # Check file
    # ---------------------

    # Read settings file and check if the setting were correctly changed
    # Creates config parser using Config to make code easier
    new_app_settings = AppSettings.load(proteus.PROTEUS_APP_PATH)

    app_settings_copy = Config().app_settings_copy

    # Check custom_profile_path setting
    assert (
        new_app_settings.custom_profile_path.as_posix()
        == new_custom_profile_path.as_posix()
        == app_settings_copy.custom_profile_path.as_posix()
    ), f"Custom profile path settings was not correctly saved. It is '{new_app_settings.custom_profile_path}' but should be '{new_custom_profile_path}' | app: {app_settings_copy.custom_profile_path}"

    # Check using_custom_profile setting
    assert (
        new_app_settings.using_default_profile
        is False
        == app_settings_copy.using_default_profile
    ), f"Using default profile settings was not correctly saved. It is '{new_app_settings.using_default_profile}' but should be 'False' | app: {app_settings_copy.using_default_profile}"
