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

import json

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
    app_settings_copy = config.app_settings_copy

    # Return settings
    yield config.app_settings

    # Restore settings
    config.app_settings.save()
    config.app_settings_copy = app_settings_copy


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


def test_config_dialog_tabs(app, app_settings: AppSettings):
    """
    Opens the config dialog and checks that the settings are grouped in
    tabs and that the advanced settings are correctly loaded.
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

    assert (
        dialog.tab_widget.count() == 3
    ), f"Settings dialog has {dialog.tab_widget.count()} tabs but should have 3"

    assert (
        dialog.developer_features_checkbox.isChecked()
        == app_settings.developer_features
    ), "Developer features checkbox does not match the settings"

    assert (
        dialog.xslt_debug_mode_checkbox.isChecked() == app_settings.xslt_debug_mode
    ), "XSLT debug mode checkbox does not match the settings"

    assert (
        dialog.mcp_enabled_checkbox.isChecked() == app_settings.mcp_server_enabled
    ), "MCP enabled checkbox does not match the settings"

    assert (
        dialog.mcp_host_edit.text() == app_settings.mcp_server_host
    ), f"MCP host is '{dialog.mcp_host_edit.text()}' but should be '{app_settings.mcp_server_host}'"

    assert (
        dialog.mcp_port_spinbox.value() == app_settings.mcp_server_port
    ), f"MCP port is '{dialog.mcp_port_spinbox.value()}' but should be '{app_settings.mcp_server_port}'"

    dialog.deleteLater()


def test_config_dialog_mcp_widgets(app, app_settings: AppSettings):
    """
    Opens the config dialog and checks that host and port are only enabled
    when the MCP server is enabled, that the warning is shown for non local
    hosts and that an empty host is not saved.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # --------------------------------------------
    # Act & Assert
    # --------------------------------------------

    # Disabled server
    dialog.mcp_enabled_checkbox.setChecked(False)

    assert dialog.mcp_host_edit.isEnabled() is False, "Host should be disabled"
    assert dialog.mcp_port_spinbox.isEnabled() is False, "Port should be disabled"
    assert dialog.mcp_host_warning_label.isHidden(), "Warning should be hidden"

    # Enabled server with local host
    dialog.mcp_enabled_checkbox.setChecked(True)
    dialog.mcp_host_edit.setText("localhost")

    assert dialog.mcp_host_edit.isEnabled() is True, "Host should be enabled"
    assert dialog.mcp_port_spinbox.isEnabled() is True, "Port should be enabled"
    assert dialog.mcp_host_warning_label.isHidden(), "Warning should be hidden"

    # Enabled server with a host reachable from the network
    dialog.mcp_host_edit.setText("0.0.0.0")

    assert (
        not dialog.mcp_host_warning_label.isHidden()
    ), "Warning should be shown for a non local host"

    # Empty host is not saved and the advanced tab is shown
    dialog.tab_widget.setCurrentWidget(dialog.general_tab)
    dialog.mcp_host_edit.setText("")
    dialog.accept_button.click()

    assert (
        not dialog.error_mcp_label.isHidden()
    ), "Empty host error should be shown"

    assert (
        dialog.tab_widget.currentWidget() is dialog.advanced_tab
    ), "Advanced tab should be shown when the MCP settings are not valid"

    assert (
        Config().app_settings_copy.mcp_server_host == app_settings.mcp_server_host
    ), "MCP settings should not be saved when the host is empty"

    dialog.close()
    dialog.deleteLater()


def test_config_dialog_change_advanced_settings(app, app_settings: AppSettings):
    """
    Opens the config dialog and changes the advanced settings. Then checks
    if the settings were correctly saved to the file.

    app_settings fixture is used to restore the settings file to its
    original state. It also works when the test fails.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    new_developer_features = not app_settings.developer_features
    new_xslt_debug_mode = not app_settings.xslt_debug_mode
    new_mcp_enabled = not app_settings.mcp_server_enabled
    new_mcp_host = "localhost"
    new_mcp_port = 9000

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # Change the advanced settings
    dialog.developer_features_checkbox.setChecked(new_developer_features)
    dialog.xslt_debug_mode_checkbox.setChecked(new_xslt_debug_mode)
    dialog.mcp_enabled_checkbox.setChecked(new_mcp_enabled)
    dialog.mcp_host_edit.setText(new_mcp_host)
    dialog.mcp_port_spinbox.setValue(new_mcp_port)

    # Save settings
    warning_dialog: MessageBox = get_dialog(dialog.accept_button.click)
    warning_dialog.button(QMessageBox.StandardButton.Ok).click()
    dialog.deleteLater()
    warning_dialog.deleteLater()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Read settings file and check if the setting were correctly changed
    new_app_settings = AppSettings.load(proteus.PROTEUS_APP_PATH)

    assert new_app_settings.developer_features == new_developer_features
    assert new_app_settings.xslt_debug_mode == new_xslt_debug_mode
    assert new_app_settings.mcp_server_enabled == new_mcp_enabled
    assert new_app_settings.mcp_server_host == new_mcp_host
    assert new_app_settings.mcp_server_port == new_mcp_port


def test_config_dialog_generate_mcp_client_config(
    app, app_settings: AppSettings, mocker, tmp_path
):
    """
    Opens the config dialog and generates the .mcp.json file in the selected
    folder using the host and port of the dialog.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Get config button
    settings_button = main_window.main_menu.settings_button

    mocker.patch(
        "proteus.views.components.dialogs.settings_dialog.QFileDialog.getExistingDirectory",
        return_value=tmp_path.as_posix(),
    )
    information = mocker.patch(
        "proteus.views.components.dialogs.settings_dialog.MessageBox.information"
    )

    # Open config dialog
    dialog: SettingsDialog = get_dialog(settings_button.click)

    # --------------------------------------------
    # Act
    # --------------------------------------------

    dialog.mcp_enabled_checkbox.setChecked(False)
    button_enabled_when_disabled = dialog.mcp_client_config_button.isEnabled()

    dialog.mcp_enabled_checkbox.setChecked(True)
    dialog.mcp_host_edit.setText("0.0.0.0")
    dialog.mcp_port_spinbox.setValue(9000)
    dialog.mcp_client_config_button.click()

    dialog.close()
    dialog.deleteLater()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    assert (
        button_enabled_when_disabled is False
    ), "Generate .mcp.json button should be disabled when the server is disabled"

    config_path = tmp_path / ".mcp.json"
    assert config_path.exists(), f"Expected file '{config_path}' to exist"

    url = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"][
        "proteus"
    ]["url"]
    assert (
        url == "http://127.0.0.1:9000/mcp/"
    ), f"Expected URL 'http://127.0.0.1:9000/mcp/', but got '{url}'"

    information.assert_called_once()
