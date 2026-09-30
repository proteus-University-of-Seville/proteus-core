# ==========================================================================
# File: test_theme_service.py
# Description: pytest file for the PROTEUS theme service (live theme
#              application: stylesheet, search paths, icon cascade and
#              theme changed event).
# Date: 12/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Generator
from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QApplication

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_APP_PATH
from proteus.application import THEME_SEARCH_PATH
from proteus.application.resources.themes import Themes
from proteus.application.resources.themes import ThemeService
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.events import ThemeChangedEvent

# --------------------------------------------------------------------------
# Global variables and constants
# --------------------------------------------------------------------------

REAL_THEMES_DIRECTORY: Path = PROTEUS_APP_PATH / "resources" / "themes"


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def theme_service(qapp: QApplication) -> Generator[ThemeService, None, None]:
    """
    ThemeService fixture with the real application themes directory loaded.

    Singletons are reset before and after each test. The global state the
    service mutates (application stylesheet and "theme:" search paths) is
    restored after each test to avoid cross-test pollution.
    """
    for singleton in (Themes, Icons, ThemeService):
        singleton._instances.pop(singleton, None)

    previous_stylesheet = qapp.styleSheet()
    previous_search_paths = QDir.searchPaths(THEME_SEARCH_PATH)

    Themes().load_themes(REAL_THEMES_DIRECTORY)

    yield ThemeService()

    qapp.setStyleSheet(previous_stylesheet)
    QDir.setSearchPaths(THEME_SEARCH_PATH, previous_search_paths)
    for singleton in (Themes, Icons, ThemeService):
        singleton._instances.pop(singleton, None)


# --------------------------------------------------------------------------
# Icons.clear tests
# --------------------------------------------------------------------------
def test_icons_clear_resets_paths_and_memo():
    """
    Icons.clear() empties both the loaded paths and the memoized QIcons.
    """
    icons = Icons()

    icons._icons_paths[ProteusIconType.App] = {"key": Path("/tmp/icon.png")}
    icons._icons_memo[ProteusIconType.App]["key"] = Icons().icon

    icons.clear()

    assert icons._icons_paths == {}
    assert all(memo == {} for memo in icons._icons_memo.values())


# --------------------------------------------------------------------------
# apply_theme tests
# --------------------------------------------------------------------------
def test_apply_theme_applies_stylesheet(theme_service: ThemeService, qapp: QApplication):
    """
    Applying the dark theme sets the application stylesheet to the rendered
    dark template (no unresolved tokens, dark window color present).
    """
    assert theme_service.apply_theme("dark")

    stylesheet = qapp.styleSheet()
    assert "#2b2b2b" in stylesheet
    assert "@" not in stylesheet or "url(" in stylesheet  # no raw @tokens


def test_apply_theme_registers_search_paths(theme_service: ThemeService):
    """
    The "theme:" search path is registered with the active theme first and
    the baseline theme as fallback.
    """
    assert theme_service.apply_theme("dark")

    search_paths = QDir.searchPaths(THEME_SEARCH_PATH)
    assert len(search_paths) == 2
    assert search_paths[0].endswith("themes/dark")
    assert search_paths[1].endswith("themes/light")


def test_apply_theme_reloads_icons(theme_service: ThemeService):
    """
    The icon cascade reloads the baseline icons, so icon keys resolve after
    applying a theme.
    """
    assert theme_service.apply_theme("light")

    icons = Icons()
    assert icons._icons_paths.get(ProteusIconType.App) is not None
    assert len(icons._icons_paths[ProteusIconType.App]) > 0


def test_apply_theme_emits_event(theme_service: ThemeService):
    """
    ThemeChangedEvent is emitted with the applied theme key after the theme
    has been fully applied.
    """
    received_keys = []

    def _recorder(theme_key: str) -> None:
        received_keys.append(theme_key)

    ThemeChangedEvent().connect(_recorder)
    try:
        assert theme_service.apply_theme("dark")
    finally:
        ThemeChangedEvent().signal.disconnect(_recorder)

    assert received_keys == ["dark"]


def test_apply_theme_switches_between_themes(theme_service: ThemeService, qapp: QApplication):
    """
    Applying a second theme replaces the first theme's stylesheet (the
    actual live-switching behavior the Settings dialog relies on).
    """
    assert theme_service.apply_theme("dark")
    assert "#2b2b2b" in qapp.styleSheet()

    assert theme_service.apply_theme("light")
    stylesheet = qapp.styleSheet()
    assert "#2b2b2b" not in stylesheet
    assert "gainsboro" in stylesheet


def test_apply_theme_unknown_key_falls_back(theme_service: ThemeService):
    """
    An unknown key resolves through the documented fallback order (ends on
    the default light theme) instead of failing.
    """
    assert theme_service.apply_theme("does-not-exist")
    assert Themes().current_theme.key == "light"


def test_apply_theme_fails_without_loaded_themes(qapp: QApplication):
    """
    Without prior discovery, apply_theme fails cleanly.
    """
    Themes._instances.pop(Themes, None)
    ThemeService._instances.pop(ThemeService, None)

    assert not ThemeService().apply_theme("light")


@pytest.mark.parametrize("broken_qss", [None, "", "QLabel { color: @undefined; }"])
def test_failed_theme_keeps_current_state(
    theme_service: ThemeService,
    qapp: QApplication,
    tmp_path: Path,
    mocker,
    broken_qss: str | None,
):
    assert theme_service.apply_theme("light")
    themes = Themes()
    previous_theme = themes.current_theme
    previous_stylesheet = qapp.styleSheet()
    previous_paths = QDir.searchPaths(THEME_SEARCH_PATH)
    previous_icons = dict(Icons()._icons_paths)
    notify = mocker.patch.object(ThemeChangedEvent(), "notify")

    # Discovery has already succeeded; simulate a theme file becoming broken
    # before application, without touching the shipped theme directory.
    themes.available_themes["dark"].path = tmp_path
    if broken_qss is not None:
        (tmp_path / "theme.qss").write_text(broken_qss, encoding="utf-8")

    assert not theme_service.apply_theme("dark")
    assert themes.current_theme is previous_theme
    assert qapp.styleSheet() == previous_stylesheet
    assert QDir.searchPaths(THEME_SEARCH_PATH) == previous_paths
    assert Icons()._icons_paths == previous_icons
    notify.assert_not_called()


def test_theme_apply_exception_restores_current_state(
    theme_service: ThemeService, qapp: QApplication, mocker
):
    assert theme_service.apply_theme("light")
    previous_theme = Themes().current_theme
    previous_stylesheet = qapp.styleSheet()
    previous_paths = QDir.searchPaths(THEME_SEARCH_PATH)
    notify = mocker.patch.object(ThemeChangedEvent(), "notify")
    mocker.patch.object(theme_service, "_reload_icons", side_effect=RuntimeError("icons"))

    assert not theme_service.apply_theme("dark")
    assert Themes().current_theme is previous_theme
    assert qapp.styleSheet() == previous_stylesheet
    assert QDir.searchPaths(THEME_SEARCH_PATH) == previous_paths
    notify.assert_not_called()


def test_theme_switch_back_renders_identical_to_fresh_boot(
    theme_service: ThemeService, qapp: QApplication
):
    """
    Regression test (stale stylesheet artifacts): switching dark -> light
    must render pixel-identically to a fresh light boot. Qt does not undo
    stylesheet state for rules removed by the new theme (e.g. dark theme's
    QWidget base background), so ThemeService clears the stylesheet before
    applying the new one.
    """
    import hashlib
    from PyQt6.QtWidgets import (
        QWidget,
        QTabWidget,
        QFrame,
        QLabel,
        QHBoxLayout,
        QToolButton,
    )

    # Panel with the artifact-prone widgets: separator + tab pane
    panel = QWidget()
    layout = QHBoxLayout(panel)
    button = QToolButton()
    button.setText("New")
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    tabs = QTabWidget()
    tabs.addTab(QLabel("page"), "View")
    layout.addWidget(button)
    layout.addWidget(separator)
    layout.addWidget(tabs)
    panel.resize(400, 100)

    def render_hash() -> str:
        panel.ensurePolished()
        qapp.processEvents()
        image = panel.grab().toImage()
        ptr = image.bits()
        ptr.setsize(image.sizeInBytes())
        return hashlib.md5(bytes(ptr.asarray())).hexdigest()

    assert theme_service.apply_theme("light")
    fresh_light_hash = render_hash()

    assert theme_service.apply_theme("dark")
    assert render_hash() != fresh_light_hash

    assert theme_service.apply_theme("light")
    assert render_hash() == fresh_light_hash

    panel.deleteLater()


def test_metric_token_drives_widget_geometry(qapp: QApplication, tmp_path: Path):
    """
    Geometry comes from theme metrics. A theme defining a custom
    icon_size_button metric produces buttons with that icon size.
    """
    from PyQt6.QtCore import QSize
    from proteus.views.buttons import ArchetypeMenuButton

    theme_dir = tmp_path / "metric-theme"
    theme_dir.mkdir()
    (theme_dir / "theme.qss").write_text(
        "QLabel { color: @error; }", encoding="utf-8"
    )
    (theme_dir / "theme.json").write_text(
        '{"metrics": {"icon_size_button": 24}}', encoding="utf-8"
    )

    for singleton in (Themes, Icons, ThemeService):
        singleton._instances.pop(singleton, None)
    try:
        Themes().load_themes(tmp_path)
        assert ThemeService().apply_theme("metric-theme")

        button = ArchetypeMenuButton(None, "dummy-class")
        assert button.iconSize() == QSize(24, 24)
        button.deleteLater()
    finally:
        for singleton in (Themes, Icons, ThemeService):
            singleton._instances.pop(singleton, None)
