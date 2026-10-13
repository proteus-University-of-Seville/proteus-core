# ==========================================================================
# File: service.py
# Description: Apply application themes at runtime (live theme switching).
# Date: 12/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application import THEME_SEARCH_PATH
from proteus.application.utils.abstract_meta import SingletonMeta
from proteus.application.configuration.config import Config
from proteus.application.resources.themes.manager import Themes
from proteus.application.resources.icons import Icons
from proteus.application.events import ThemeChangedEvent

# logging configuration
log = logging.getLogger(__name__)


class ThemeService(metaclass=SingletonMeta):
    """
    Applies a discovered theme to the running QApplication. This is the
    single code path used both at startup and when the user switches theme
    in the Settings dialog, so runtime switching cannot diverge from the
    initial application.

    apply_theme() performs, in order:
        1. Icon cache reload (baseline theme icons, active theme delta,
           profile icons) — done BEFORE notifying so subscribers resolve
           fresh icons.
        2. "theme:" Qt search path registration (active theme first,
           baseline as fallback) for url(theme:...) QSS references.
        3. Request the Qt color scheme and restore the unthemed palette,
           with the active theme's explicit palette overrides.
        4. Application stylesheet (rendered from the theme template).
        5. ThemeChangedEvent notification.
    """

    def __init__(self) -> None:
        # Capture lazily, once a QApplication exists and before the first
        # theme application. QPalette() later inherits the active palette,
        # so it cannot be used to recover this platform/application baseline.
        self._baseline_palette: QPalette | None = None

    def apply_theme(self, theme_key: str) -> bool:
        """
        Select and apply the given theme to the running application.

        Assumes themes have already been discovered via
        Themes().load_themes(). Unknown keys fall back per
        Themes.select_theme() resolution order.

        :param theme_key: Key of the theme to apply.
        :return: True if a theme was selected and applied, False otherwise.
        """
        themes = Themes()
        metadata = themes.resolve_theme(theme_key)
        if metadata is None:
            log.error(
                f"Cannot apply theme '{theme_key}': no themes are loaded."
            )
            return False

        # Prepare before touching singleton or Qt state. A missing template or
        # unresolved token must not replace a working theme.
        stylesheet = themes.render_stylesheet(metadata)
        if not stylesheet:
            return False

        app = QApplication.instance()
        if not isinstance(app, QApplication):
            log.error("Cannot apply a theme without a QApplication instance.")
            return False

        previous_theme = themes.current_theme
        previous_stylesheet = app.styleSheet()
        previous_search_paths = QDir.searchPaths(THEME_SEARCH_PATH)
        previous_palette = app.palette()
        if self._baseline_palette is None:
            self._baseline_palette = QPalette(previous_palette)
        previous_scheme = QGuiApplication.styleHints().colorScheme()
        icons = Icons()
        previous_icon_paths = icons._icons_paths
        previous_icon_memo = icons._icons_memo
        palette_applied = False

        try:
            themes.activate_theme(metadata)

            # Reload before notifying so subscribers receive icons from the
            # new baseline -> active -> profile cascade.
            self._reload_icons()

            # QSS icon URLs fall back to the baseline when the active theme
            # supplies only a subset of assets.
            QDir.setSearchPaths(
                THEME_SEARCH_PATH,
                themes.search_path_directories(),
            )

            self._apply_color_scheme()

            palette = themes.build_palette(self._baseline_palette)
            if palette is None:
                palette = QPalette(self._baseline_palette)
            # Always replace the palette, including for QSS-only themes.
            # Clearing QSS does not undo an explicit application palette;
            # Qt also uses it to generate disabled icons and native frames.
            palette_applied = True
            app.setPalette(palette)
            log.debug(
                "Theme '%s' palette applied (overrides=%s): "
                "Window %s -> %s, Disabled.Window %s -> %s.",
                metadata.key, bool(metadata.manifest.palette),
                previous_palette.color(QPalette.ColorRole.Window).name(),
                palette.color(QPalette.ColorRole.Window).name(),
                previous_palette.color(
                    QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window
                ).name(),
                palette.color(
                    QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window
                ).name(),
            )

            # Qt can retain dark-only QWidget backgrounds when directly
            # replacing a stylesheet; clearing first resets those rules.
            app.setStyleSheet("")
            app.setStyleSheet(stylesheet)
        except Exception:
            log.exception(
                "Could not apply theme '%s'; restoring previous theme.", metadata.key
            )
            themes.activate_theme(previous_theme)
            icons._icons_paths = previous_icon_paths
            icons._icons_memo = previous_icon_memo
            QDir.setSearchPaths(THEME_SEARCH_PATH, previous_search_paths)
            QGuiApplication.styleHints().setColorScheme(previous_scheme)
            if palette_applied:
                app.setPalette(previous_palette)
            app.setStyleSheet("")
            app.setStyleSheet(previous_stylesheet)
            return False

        log.info(f"Theme '{metadata.key}' applied.")
        ThemeChangedEvent().notify(metadata.key)
        return True

    def _reload_icons(self) -> None:
        """
        Clear the icon cache and re-run the icon cascade:
            1. themes/light/icons     baseline (ALWAYS)
            2. themes/{active}/icons  delta (skipped when active IS baseline)
            3. profile/icons          profile overrides
        """
        themes = Themes()
        icons = Icons()

        icons.clear()

        # The baseline is needed even when the active theme is a delta.
        baseline_icons_dir = themes.baseline_icons_directory()
        if baseline_icons_dir is not None:
            icons.load_icons(baseline_icons_dir)
        else:
            log.error(
                "Baseline theme 'light' has no icons directory. "
                "Application icons will be incomplete."
            )

        # Avoid loading the baseline twice when it is the active theme.
        active = themes.current_theme
        baseline = themes.baseline_theme
        if (
            active is not None
            and baseline is not None
            and active.key != baseline.key
        ):
            active_icons_dir = themes.icons_directory()
            if active_icons_dir is not None:
                icons.load_icons(active_icons_dir)

        # Profile overrides have the final say, regardless of the theme.
        icons.load_icons(Config().profile_settings.icons_directory)

    def _apply_color_scheme(self) -> None:
        """
        Force the QPalette to match the theme's intended color scheme.
        Without this, the OS palette bleeds through any property the QSS
        does not explicitly set — e.g. button text color falls through to
        QPalette.ButtonText, which on a dark-mode OS is white, rendering
        text invisible against a QSS-styled light button background.
        """
        scheme = Themes().qt_color_scheme()
        if scheme == Qt.ColorScheme.Unknown:
            return

        if QApplication.instance() is None:
            log.debug("No QApplication instance, skipping color scheme.")
            return

        style_hints = QGuiApplication.styleHints()
        if style_hints is None:
            log.debug("No QStyleHints available, skipping color scheme.")
            return

        if hasattr(style_hints, "setColorScheme"):
            try:
                style_hints.setColorScheme(scheme)
                log.info(f"Forced application color scheme to '{scheme.name}'.")
            except Exception as e:
                log.warning(
                    f"Could not set color scheme '{scheme.name}': {e}. "
                    "Theme will rely on stylesheet only; widgets that fall "
                    "through to QPalette may look wrong."
                )
        else:
            log.warning(
                "QStyleHints.setColorScheme is unavailable on this Qt build. "
                "Theme will rely on stylesheet only."
            )
