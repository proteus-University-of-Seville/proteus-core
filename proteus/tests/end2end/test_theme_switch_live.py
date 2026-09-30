# ==========================================================================
# File: test_theme_switch_live.py
# Description: pytest file for live theme switching through the Settings
#              dialog (theme applies without restart and components
#              refresh their icons).
# Date: 12/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Generator
from unittest.mock import patch

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QApplication

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_APP_PATH
from proteus.application import THEME_SEARCH_PATH
from proteus.application.configuration.config import Config
from proteus.application.configuration.app_settings import AppSettings
from proteus.application.resources.themes import Themes
from proteus.application.resources.themes import ThemeService
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.events import ThemeChangedEvent
from proteus.views.components.main_window import MainWindow
from proteus.views.components.dialogs.settings_dialog import SettingsDialog
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.tests.end2end.fixtures import app, get_dialog
from proteus.tests.end2end.fixtures import load_project

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

REAL_THEMES_DIRECTORY = PROTEUS_APP_PATH / "resources" / "themes"
DARK_WINDOW_COLOR = "#2b2b2b"


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture(scope="function")
def app_settings():
    """
    Snapshot the live AppSettings before the test and restore them after,
    covering BOTH the live Config singleton and the persisted proteus.ini
    (saving from the Settings dialog mutates both). The staging object
    app_settings_copy is restored as well, since saves persist into it
    across tests within a session.
    """
    config = Config()
    snapshot = config.app_settings
    snapshot_copy = config.app_settings_copy
    yield snapshot
    config.app_settings = snapshot
    config.app_settings_copy = snapshot_copy
    snapshot.save()


@pytest.fixture(scope="function")
def theme_state(qapp: QApplication) -> Generator[None, None, None]:
    """
    Load the real themes and snapshot the global Qt state mutated by theme
    application (stylesheet and "theme:" search paths), restoring it after
    the test. Themes/ThemeService singletons are reset afterwards.
    """
    previous_stylesheet = qapp.styleSheet()
    previous_search_paths = QDir.searchPaths(THEME_SEARCH_PATH)

    themes = Themes()
    if not themes.available_themes:
        themes.load_themes(REAL_THEMES_DIRECTORY)
    themes.select_theme("light")

    yield

    # Flush deferred dialog deletions before a global stylesheet repolish.
    qapp.processEvents()
    qapp.setStyleSheet(previous_stylesheet)
    QDir.setSearchPaths(THEME_SEARCH_PATH, previous_search_paths)
    for singleton in (Themes, ThemeService):
        singleton._instances.pop(singleton, None)


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------
def test_theme_switch_applies_live_without_restart_warning(
    app, app_settings, theme_state, mocker
):
    """
    Changing only the theme in the Settings dialog applies it live (dark
    stylesheet set, ThemeChangedEvent emitted, components re-query icons)
    and does NOT show the restart warning.
    """
    main_window: MainWindow = app

    received_keys = []
    ThemeChangedEvent().connect(received_keys.append)

    # Mock the restart warning so the test cannot hang on a modal dialog
    warning_mock = mocker.patch.object(MessageBox, "warning")

    dialog: SettingsDialog = get_dialog(main_window.main_menu.settings_button.click)

    dark_index: int = dialog.theme_combo.findData("dark")
    assert dark_index >= 0, "Dark theme not found in settings combo"
    dialog.theme_combo.setCurrentIndex(dark_index)

    # Force a clean baseline: align the current settings with the dialog's
    # staged copy (except the theme) so the only detected change is the
    # theme. This isolates the test from configuration drift left by
    # previous tests in the batch.
    Config().app_settings = Config().app_settings_copy.clone(theme="light")

    dialog.accept_button.click()

    try:
        stylesheet: str = QApplication.instance().styleSheet()
        assert DARK_WINDOW_COLOR in stylesheet, "Dark stylesheet not applied"
        assert Themes().current_theme.key == "dark"

        assert "dark" in received_keys

        # The memo repopulates only when components re-query their icons.
        assert len(Icons()._icons_memo[ProteusIconType.MainMenu]) > 0

        warning_mock.assert_not_called()
    finally:
        ThemeChangedEvent().signal.disconnect(received_keys.append)


def test_theme_plus_other_setting_still_shows_restart_warning(
    app, app_settings, theme_state, mocker
):
    """
    Changing the theme AND another setting applies the theme live but
    still shows the restart warning for the remaining settings.
    """
    main_window: MainWindow = app
    warning_mock = mocker.patch.object(MessageBox, "warning")

    dialog: SettingsDialog = get_dialog(main_window.main_menu.settings_button.click)

    dark_index: int = dialog.theme_combo.findData("dark")
    dialog.theme_combo.setCurrentIndex(dark_index)

    # Change the language as well (guaranteed to differ from current)
    language_combo = dialog.language_combo
    new_language_index: int = (language_combo.currentIndex() + 1) % language_combo.count()
    language_combo.setCurrentIndex(new_language_index)

    dialog.accept_button.click()

    assert DARK_WINDOW_COLOR in QApplication.instance().styleSheet()

    warning_mock.assert_called_once()


def test_theme_can_switch_back_and_forth_in_one_session(
    app, app_settings, theme_state, mocker
):
    """
    Regression test (stale baseline bug): the theme must switch on EVERY
    save, not only on the first one of the session. Before the fix, the
    change was detected against a boot-time snapshot of the settings, so
    only the first change per session was applied.
    """
    main_window: MainWindow = app
    mocker.patch.object(MessageBox, "warning")

    def save_theme(theme_key: str) -> None:
        dialog: SettingsDialog = get_dialog(
            main_window.main_menu.settings_button.click
        )
        index: int = dialog.theme_combo.findData(theme_key)
        assert index >= 0, f"Theme '{theme_key}' not found in settings combo"
        dialog.theme_combo.setCurrentIndex(index)
        dialog.accept_button.click()

    save_theme("dark")
    assert Themes().current_theme.key == "dark"
    assert DARK_WINDOW_COLOR in QApplication.instance().styleSheet()

    save_theme("light")
    assert Themes().current_theme.key == "light"
    assert DARK_WINDOW_COLOR not in QApplication.instance().styleSheet()

    save_theme("dark")
    assert Themes().current_theme.key == "dark"
    assert DARK_WINDOW_COLOR in QApplication.instance().styleSheet()


def test_restart_warning_not_repeated_on_unchanged_save(
    app, app_settings, theme_state, mocker
):
    """
    Regression test (restart warning policy): the warning is shown on the
    save that introduces a change requiring restart, but NOT on subsequent
    saves that change nothing, even while the restart is still pending.
    """
    main_window: MainWindow = app
    warning_mock = mocker.patch.object(MessageBox, "warning")

    dialog: SettingsDialog = get_dialog(main_window.main_menu.settings_button.click)

    language_combo = dialog.language_combo
    new_language_index: int = (language_combo.currentIndex() + 1) % language_combo.count()
    language_combo.setCurrentIndex(new_language_index)

    dialog.accept_button.click()

    warning_mock.assert_called_once()

    warning_mock.reset_mock()

    second_dialog: SettingsDialog = get_dialog(
        main_window.main_menu.settings_button.click
    )
    second_dialog.accept_button.click()

    warning_mock.assert_not_called()


def test_theme_only_save_does_not_warn_while_restart_pending(
    app, app_settings, theme_state, mocker
):
    """
    Regression test (theme-excluded warning policy): after a save that
    introduced a change requiring restart (language), a subsequent
    THEME-ONLY save must not warn again — the theme is applied live and
    never requires a restart, so it must be ignored by both warning
    conditions.
    """
    main_window: MainWindow = app
    warning_mock = mocker.patch.object(MessageBox, "warning")

    dialog: SettingsDialog = get_dialog(main_window.main_menu.settings_button.click)

    language_combo = dialog.language_combo
    new_language_index: int = (language_combo.currentIndex() + 1) % language_combo.count()
    language_combo.setCurrentIndex(new_language_index)

    dialog.accept_button.click()

    warning_mock.assert_called_once()
    warning_mock.reset_mock()

    second_dialog: SettingsDialog = get_dialog(
        main_window.main_menu.settings_button.click
    )
    dark_index: int = second_dialog.theme_combo.findData("dark")
    assert dark_index >= 0, "Dark theme not found in settings combo"
    second_dialog.theme_combo.setCurrentIndex(dark_index)

    second_dialog.accept_button.click()

    assert Themes().current_theme.key == "dark"
    warning_mock.assert_not_called()


def test_failed_theme_save_keeps_dialog_and_persisted_choice(
    app, app_settings, theme_state, mocker, tmp_path
):
    assert ThemeService().apply_theme("light")
    previous_stylesheet = QApplication.instance().styleSheet()
    previous_settings = Config().app_settings_copy
    previous_file = previous_settings.settings_file_path.read_bytes()
    warning = mocker.patch.object(MessageBox, "warning")

    # Keep discovery intact but break the stylesheet before Settings saves.
    Themes().available_themes["dark"].path = tmp_path
    dialog = get_dialog(app.main_menu.settings_button.click)
    delete_later = mocker.spy(dialog, "deleteLater")
    dialog.theme_combo.setCurrentIndex(dialog.theme_combo.findData("dark"))
    dialog.accept_button.click()

    # get_dialog hides modal widgets; remaining usable means no deletion was
    # scheduled by the failed save.
    delete_later.assert_not_called()
    assert Themes().current_theme.key == "light"
    assert QApplication.instance().styleSheet() == previous_stylesheet
    assert Config().app_settings_copy is previous_settings
    assert previous_settings.settings_file_path.read_bytes() == previous_file
    warning.assert_called_once()
    dialog.close()
    dialog.deleteLater()


def test_project_container_widths_follow_theme_metrics(app, theme_state):
    assert ThemeService().apply_theme("light")
    load_project(main_window=app)
    container = app.project_container
    assert container.documents_container.minimumWidth() == 200
    assert container.views_container.minimumWidth() == 400

    Themes().available_themes["dark"].manifest.metrics.update(
        tree_min_width=275, views_min_width=525
    )
    assert ThemeService().apply_theme("dark")
    assert container.documents_container.minimumWidth() == 275
    assert container.views_container.minimumWidth() == 525

    assert ThemeService().apply_theme("light")
    assert container.documents_container.minimumWidth() == 200
    assert container.views_container.minimumWidth() == 400


def test_failed_settings_write_restores_applied_theme(
    app, app_settings, theme_state, mocker
):
    assert ThemeService().apply_theme("light")
    previous_stylesheet = QApplication.instance().styleSheet()
    previous_settings = Config().app_settings_copy
    warning = mocker.patch.object(MessageBox, "warning")

    dialog = get_dialog(app.main_menu.settings_button.click)
    delete_later = mocker.spy(dialog, "deleteLater")
    dialog.theme_combo.setCurrentIndex(dialog.theme_combo.findData("dark"))
    with patch.object(AppSettings, "save", side_effect=OSError("disk full")):
        dialog.accept_button.click()

    assert Themes().current_theme.key == "light"
    assert QApplication.instance().styleSheet() == previous_stylesheet
    assert Config().app_settings_copy is previous_settings
    assert Config().app_settings_copy.config_parser["settings"]["theme"] == "light"
    delete_later.assert_not_called()
    warning.assert_called_once()
    dialog.close()
    dialog.deleteLater()
