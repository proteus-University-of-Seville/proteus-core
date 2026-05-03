# ==========================================================================
# File: themes.py
# Description: Manage the visual themes for PROTEUS application.
# Date: 03/05/2026
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import json
import logging
from pathlib import Path
from typing import Dict, List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

THEMES_DIRECTORY: str = "themes"
THEME_QSS_FILE: str = "theme.qss"
THEME_STATE_COLORS_FILE: str = "state_colors.json"
THEME_ICONS_MANIFEST: str = "icons.xml"

# Theme key used as the fallback default when AppSettings.theme is unset or
# refers to a theme that no longer exists.
DEFAULT_THEME_KEY: str = "light"

DEFAULT_STATE_COLORS: Dict[str, str] = {
    "fresh": "#006400",
    "dirty": "#B8860B",
    "dead":  "#8B0000",
    "clean": "#000000",
}


# --------------------------------------------------------------------------
# Helpers (folder name → derived metadata)
# --------------------------------------------------------------------------
def _derive_display_name(key: str) -> str:
    """
    Convert a folder name into a human-readable display name.

    Hyphens and underscores become spaces; words are title-cased.
    Examples:
        "light"           -> "Light"
        "gruvbox-dark"    -> "Gruvbox Dark"
        "solarized_light" -> "Solarized Light"
    """
    cleaned = key.replace("-", " ").replace("_", " ").strip()
    return cleaned.title() if cleaned else key


def _derive_color_scheme(key: str) -> str:
    """
    Heuristic: infer the theme's intended color scheme from its folder name.

    A folder whose name contains "dark" (case-insensitive) is treated as a
    dark theme; one containing "light" is treated as light. Anything else
    returns None — palette is left to the OS.

    This lets community themes named like "gruvbox-dark" or "solarized-light"
    pick up the correct QPalette without any metadata file.
    """
    lower = key.lower()
    if "dark" in lower:
        return "dark"
    if "light" in lower:
        return "light"
    return None


# --------------------------------------------------------------------------
# Class: ThemeMetadata
# --------------------------------------------------------------------------
class ThemeMetadata:
    """
    In-memory record describing a discovered theme.

    All fields are derived from the theme's folder; there is no metadata
    file in v1. ``color_scheme`` is a string ("light", "dark") or None
    when the folder name doesn't suggest one. Use Themes.qt_color_scheme()
    to resolve to a Qt.ColorScheme enum value.
    """

    __slots__ = ("key", "path", "name", "color_scheme")

    def __init__(self, key: str, path: Path, name: str, color_scheme: str = None):
        self.key: str = key
        self.path: Path = path
        self.name: str = name
        self.color_scheme: str = color_scheme


# --------------------------------------------------------------------------
# Class: Themes
# Description: Manage the visual themes for PROTEUS application.
# --------------------------------------------------------------------------
class Themes(metaclass=SingletonMeta):
    """
    Singleton that discovers themes shipped under resources/themes and
    resolves the active theme based on the user setting (with fallbacks).

    Discovery is convention-based — there is no manifest. Any subdirectory
    of the configured themes root that contains ``theme.qss`` is treated
    as a theme; the folder name is the stable id used in proteus.ini and
    in the Settings dialog. Themes are listed in alphabetical order.

    A theme directory may also contain:
        - state_colors.json      document-tree state colors
        - icons.xml + icons/...  icon overrides (delta against the
                                 baseline theme)

    Resolution order on select_theme(requested_key):
        1. The requested key, if present.
        2. The hardcoded default ("light"), if present.
        3. The first theme in alphabetical order.

    color_scheme is inferred from the folder name (substring "dark" or
    "light"); themes with neither leave the palette to the OS.
    """

    # ----------------------------------------------------------------------
    # Method: __init__
    # ----------------------------------------------------------------------
    def __init__(self):
        self._themes_directory: Path = None
        self._available_themes: Dict[str, ThemeMetadata] = {}
        self._current_theme: ThemeMetadata = None

    # ==========================================================================
    # Public API
    # ==========================================================================

    # ----------------------------------------------------------------------
    # Method: load_themes
    # ----------------------------------------------------------------------
    def load_themes(self, themes_directory: Path) -> bool:
        """
        Discover themes by scanning the given directory. A subdirectory
        is treated as a theme if and only if it contains ``theme.qss``.

        Repeated calls reset the discovered themes (does not stack).

        :param themes_directory: Path to the directory holding one
            subdirectory per theme.
        :return: True if at least one theme was discovered, False otherwise.
        """
        self._available_themes = {}
        self._current_theme = None
        self._themes_directory = None

        if themes_directory is None:
            log.error("Themes directory is None.")
            return False

        if not themes_directory.exists() or not themes_directory.is_dir():
            log.error(f"Themes directory '{themes_directory}' does not exist.")
            return False

        self._themes_directory = themes_directory

        # Alphabetical iteration so first-found fallback and Settings combo
        # ordering are deterministic across platforms.
        for entry in sorted(themes_directory.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir():
                continue

            qss_path = entry / THEME_QSS_FILE
            if not qss_path.exists():
                log.debug(
                    f"Skipping '{entry.name}' — no {THEME_QSS_FILE} present."
                )
                continue

            key = entry.name
            self._available_themes[key] = ThemeMetadata(
                key=key,
                path=entry,
                name=_derive_display_name(key),
                color_scheme=_derive_color_scheme(key),
            )

        if not self._available_themes:
            log.error(f"No themes were discovered in '{themes_directory}'.")
            return False

        log.info(f"Discovered themes: {list(self._available_themes.keys())}")
        return True

    # ----------------------------------------------------------------------
    # Method: select_theme
    # ----------------------------------------------------------------------
    def select_theme(self, requested_key: str) -> ThemeMetadata:
        """
        Choose the active theme using the documented resolution order.
        Returns the resolved ThemeMetadata (also cached as current_theme).

        :param requested_key: User-requested theme key (typically from
            proteus.ini). May be None or unknown — fallbacks apply.
        """
        if not self._available_themes:
            log.error("select_theme called but no themes have been loaded.")
            self._current_theme = None
            return None

        # 1) Requested key
        if requested_key and requested_key in self._available_themes:
            self._current_theme = self._available_themes[requested_key]
            log.info(f"Selected theme '{self._current_theme.key}' (requested).")
            return self._current_theme

        if requested_key:
            log.warning(
                f"Requested theme '{requested_key}' is not available. "
                f"Trying default '{DEFAULT_THEME_KEY}'."
            )

        # 2) Hardcoded default ("light")
        if DEFAULT_THEME_KEY in self._available_themes:
            self._current_theme = self._available_themes[DEFAULT_THEME_KEY]
            log.info(f"Selected theme '{self._current_theme.key}' (default).")
            return self._current_theme

        # 3) First available, alphabetical
        first_key = next(iter(self._available_themes))
        self._current_theme = self._available_themes[first_key]
        log.info(
            f"Selected theme '{self._current_theme.key}' (first available)."
        )
        return self._current_theme

    # ----------------------------------------------------------------------
    # Property: available_themes
    # ----------------------------------------------------------------------
    @property
    def available_themes(self) -> Dict[str, ThemeMetadata]:
        """Return a dict of all discovered themes keyed by theme key."""
        return dict(self._available_themes)

    # ----------------------------------------------------------------------
    # Property: current_theme
    # ----------------------------------------------------------------------
    @property
    def current_theme(self) -> ThemeMetadata:
        """The currently selected ThemeMetadata, or None."""
        return self._current_theme

    # ----------------------------------------------------------------------
    # Property: themes_directory
    # ----------------------------------------------------------------------
    @property
    def themes_directory(self) -> Path:
        """The root themes directory passed to load_themes."""
        return self._themes_directory

    # ----------------------------------------------------------------------
    # Method: stylesheet
    # ----------------------------------------------------------------------
    def stylesheet(self) -> str:
        """
        Read theme.qss for the current theme and return its content.
        Returns empty string if no current theme is selected or the file
        cannot be read (errors are logged).
        """
        if self._current_theme is None:
            log.error("stylesheet() called but no theme is selected.")
            return ""

        qss_path: Path = self._current_theme.path / THEME_QSS_FILE
        try:
            return qss_path.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Error reading theme stylesheet '{qss_path}': {e}")
            return ""

    # ----------------------------------------------------------------------
    # Method: state_colors
    # ----------------------------------------------------------------------
    def state_colors(self) -> Dict[str, QColor]:
        """
        Return the document-tree state colors for the current theme as
        {state_name: QColor}. Falls back to DEFAULT_STATE_COLORS for any
        missing key (so a partial state_colors.json is still safe).
        """
        merged: Dict[str, str] = dict(DEFAULT_STATE_COLORS)

        if self._current_theme is not None:
            colors_path: Path = self._current_theme.path / THEME_STATE_COLORS_FILE
            if colors_path.exists():
                try:
                    raw = json.loads(colors_path.read_text(encoding="utf-8"))
                    if isinstance(raw, dict):
                        for k, v in raw.items():
                            if isinstance(k, str) and isinstance(v, str):
                                merged[k.lower()] = v
                    else:
                        log.error(
                            f"State colors file '{colors_path}' is not a JSON "
                            "object. Using defaults."
                        )
                except Exception as e:
                    log.error(
                        f"Error parsing state colors file '{colors_path}': {e}. "
                        "Using defaults."
                    )

        result: Dict[str, QColor] = {}
        for k, v in merged.items():
            color = QColor(v)
            if not color.isValid():
                log.warning(
                    f"Invalid color '{v}' for state '{k}'. Using default."
                )
                color = QColor(DEFAULT_STATE_COLORS.get(k, "#000000"))
            result[k] = color
        return result

    # ----------------------------------------------------------------------
    # Method: icons_directory
    # ----------------------------------------------------------------------
    def icons_directory(self) -> Path:
        """
        Return the icons directory of the current theme — the ``icons/``
        subdirectory inside the theme, which holds ``icons.xml`` plus the
        theme's icon assets. Returns None if no theme is selected or the
        theme does not ship an icons manifest.

        This convention matches the app and profile icon directories, so
        ``Icons.load_icons(...)`` accepts any of the three layers
        identically.
        """
        if self._current_theme is None:
            return None
        icons_dir = self._current_theme.path / "icons"
        manifest = icons_dir / THEME_ICONS_MANIFEST
        if not manifest.exists():
            return None
        return icons_dir

    # ----------------------------------------------------------------------
    # Method: qt_color_scheme
    # ----------------------------------------------------------------------
    def qt_color_scheme(self) -> "Qt.ColorScheme":
        """
        Resolve the current theme's color_scheme to a Qt.ColorScheme enum.
        Returns Qt.ColorScheme.Unknown when the heuristic could not infer
        a scheme — caller should treat this as "do not force the palette".
        """
        if self._current_theme is None or self._current_theme.color_scheme is None:
            return Qt.ColorScheme.Unknown

        scheme = self._current_theme.color_scheme
        if scheme == "light":
            return Qt.ColorScheme.Light
        if scheme == "dark":
            return Qt.ColorScheme.Dark
        return Qt.ColorScheme.Unknown

    # ----------------------------------------------------------------------
    # Property: baseline_theme
    # ----------------------------------------------------------------------
    @property
    def baseline_theme(self) -> ThemeMetadata:
        """
        The canonical baseline theme — the one that ships every visual
        asset and that other themes are deltas of. Resolved by looking
        up DEFAULT_THEME_KEY ("light") in the discovered themes; returns
        None if the baseline is somehow missing.
        """
        return self._available_themes.get(DEFAULT_THEME_KEY)

    # ----------------------------------------------------------------------
    # Method: baseline_icons_directory
    # ----------------------------------------------------------------------
    def baseline_icons_directory(self) -> Path:
        """
        Return the icons directory of the baseline theme, or None if the
        baseline is missing or has no icons manifest. Used by the app
        bootstrap to load the full icon set before any theme delta.
        """
        baseline = self.baseline_theme
        if baseline is None:
            return None
        icons_dir = baseline.path / "icons"
        if not (icons_dir / THEME_ICONS_MANIFEST).exists():
            return None
        return icons_dir

    # ----------------------------------------------------------------------
    # Method: search_path_directories
    # ----------------------------------------------------------------------
    def search_path_directories(self) -> List[str]:
        """
        Return the directories to register under the "theme:" Qt search
        path, in priority order: the active theme directory first, then
        the baseline theme directory as fallback. ``url(theme:icons/...)``
        references in QSS resolve against this list, so a theme that
        doesn't ship a particular icon falls through to the baseline.
        """
        paths: List[str] = []
        if self._current_theme is not None:
            paths.append(self._current_theme.path.as_posix())

        baseline = self.baseline_theme
        if baseline is not None and (
            self._current_theme is None
            or self._current_theme.key != baseline.key
        ):
            paths.append(baseline.path.as_posix())

        return paths
