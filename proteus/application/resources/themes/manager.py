# ==========================================================================
# File: manager.py
# Description: Manage the visual themes for PROTEUS application.
# Date: 13/09/2026
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Dict, List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta
from proteus.application.resources.themes.manifest import (
    ThemeManifest,
    THEME_MANIFEST_FILE,
    DEFAULT_STATE_COLORS,
    TOKEN_PATTERN,
    render_qss,
)

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

THEMES_DIRECTORY: str = "themes"
THEME_QSS_FILE: str = "theme.qss"
THEME_ICONS_MANIFEST: str = "icons.xml"

# Theme key used as the fallback default when AppSettings.theme is unset or
# refers to a theme that no longer exists.
DEFAULT_THEME_KEY: str = "light"

# Legacy v1 file, superseded by the "state_colors" section of theme.json.
_LEGACY_STATE_COLORS_FILE: str = "state_colors.json"


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
    returns None, so no color scheme is requested for that theme.

    This lets themes named like "gruvbox-dark" or "solarized-light" pick up
    a color scheme when their manifest does not specify one.
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

    ``name`` and ``color_scheme`` come from the theme.json manifest, falling
    back to folder-name derivation when the manifest omits them. ``manifest``
    holds the parsed ThemeManifest (tokens, metrics, state colors, palette).
    """

    __slots__ = ("key", "path", "name", "color_scheme", "manifest")

    def __init__(
        self,
        key: str,
        path: Path,
        name: str,
        manifest: ThemeManifest,
        color_scheme: str = None,
    ):
        self.key: str = key
        self.path: Path = path
        self.name: str = name
        self.color_scheme: str = color_scheme
        self.manifest: ThemeManifest = manifest


# --------------------------------------------------------------------------
# Class: Themes
# Description: Manage the visual themes for PROTEUS application.
# --------------------------------------------------------------------------
class Themes(metaclass=SingletonMeta):
    """
    Singleton that discovers themes shipped under resources/themes and
    resolves the active theme based on the user setting (with fallbacks).

    Discovery is convention-based. Any subdirectory of the configured themes
    root that contains a valid ``theme.json`` manifest AND a ``theme.qss``
    template is treated as a theme; the folder name is the stable id used in
    proteus.ini and in the Settings dialog. Themes are listed in alphabetical
    order.

    A theme directory may also contain:
        - icons/icons.xml + icons/...  icon overrides against the
                                       baseline theme

    The manifest provides the token namespace used to render the QSS
    template (see manifest.py for the schema), plus state colors,
    metrics and an optional QPalette mapping.

    Resolution order on select_theme(requested_key):
        1. The requested key, if present.
        2. The hardcoded default ("light"), if present.
        3. The first theme in alphabetical order.

    color_scheme comes from the manifest, falling back to a folder-name
    heuristic (substring "dark" or "light"); themes with neither do not
    request a Qt color scheme.
    """

    def __init__(self):
        self._themes_directory: Path = None
        self._available_themes: Dict[str, ThemeMetadata] = {}
        self._current_theme: ThemeMetadata = None

    # ==========================================================================
    # Public API
    # ==========================================================================

    def load_themes(self, themes_directory: Path) -> bool:
        """
        Discover themes by scanning the given directory. A subdirectory
        is treated as a theme if and only if it contains a valid
        ``theme.json`` manifest AND a ``theme.qss`` template.

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

            # A QSS-only directory is not a valid theme in format v2.
            manifest = ThemeManifest.load(entry / THEME_MANIFEST_FILE)
            if manifest is None:
                log.warning(
                    f"Skipping '{entry.name}' — a valid {THEME_MANIFEST_FILE} "
                    "is required since theme format v2."
                )
                continue

            # Legacy state_colors.json is ignored; state colors live in the
            # manifest now.
            if (entry / _LEGACY_STATE_COLORS_FILE).exists():
                log.info(
                    f"Theme '{entry.name}' ships a legacy "
                    f"'{_LEGACY_STATE_COLORS_FILE}' file. It is ignored — "
                    f"move its colors into the 'state_colors' section of "
                    f"{THEME_MANIFEST_FILE}."
                )

            key = entry.name
            self._available_themes[key] = ThemeMetadata(
                key=key,
                path=entry,
                name=manifest.name or _derive_display_name(key),
                color_scheme=manifest.color_scheme or _derive_color_scheme(key),
                manifest=manifest,
            )

        if not self._available_themes:
            log.error(f"No themes were discovered in '{themes_directory}'.")
            return False

        log.info(f"Discovered themes: {list(self._available_themes.keys())}")
        return True

    def select_theme(self, requested_key: str) -> ThemeMetadata:
        """
        Choose the active theme using the documented resolution order.
        Returns the resolved ThemeMetadata (also cached as current_theme).

        :param requested_key: User-requested theme key (typically from
            proteus.ini). May be None or unknown — fallbacks apply.
        """
        self._current_theme = self.resolve_theme(requested_key)
        return self._current_theme

    def activate_theme(self, metadata: ThemeMetadata | None) -> None:
        """Commit a prepared theme, or restore a previous selection on failure."""
        self._current_theme = metadata

    def resolve_theme(self, requested_key: str) -> ThemeMetadata | None:
        """Resolve a theme using the normal fallback order without selecting it."""
        if not self._available_themes:
            log.error("select_theme called but no themes have been loaded.")
            return None

        if requested_key and requested_key in self._available_themes:
            return self._available_themes[requested_key]

        if requested_key:
            log.warning(
                f"Requested theme '{requested_key}' is not available. "
                f"Trying default '{DEFAULT_THEME_KEY}'."
            )

        if DEFAULT_THEME_KEY in self._available_themes:
            return self._available_themes[DEFAULT_THEME_KEY]

        first_key = next(iter(self._available_themes))
        return self._available_themes[first_key]

    @property
    def available_themes(self) -> Dict[str, ThemeMetadata]:
        """Return a dict of all discovered themes keyed by theme key."""
        return dict(self._available_themes)

    @property
    def current_theme(self) -> ThemeMetadata:
        """The currently selected ThemeMetadata, or None."""
        return self._current_theme

    @property
    def themes_directory(self) -> Path:
        """The root themes directory passed to load_themes."""
        return self._themes_directory

    def stylesheet(self) -> str:
        """
        Read theme.qss for the current theme and render it with the theme's
        token namespace (@token substitution). Returns empty string if no
        current theme is selected or the file cannot be read (errors are
        logged).
        """
        if self._current_theme is None:
            log.error("stylesheet() called but no theme is selected.")
            return ""
        return self.render_stylesheet(self._current_theme)

    def render_stylesheet(self, metadata: ThemeMetadata) -> str:
        """Render a candidate without selecting it; return empty on invalid QSS."""
        qss_path: Path = metadata.path / THEME_QSS_FILE
        try:
            template = qss_path.read_text(encoding="utf-8")
        except OSError as e:
            log.error(f"Error reading theme stylesheet '{qss_path}': {e}")
            return ""

        if not template.strip():
            log.error(f"Theme stylesheet '{qss_path}' is empty.")
            return ""
        stylesheet = render_qss(template, metadata.manifest.tokens())
        if TOKEN_PATTERN.search(stylesheet):
            log.error(f"Theme stylesheet '{qss_path}' contains unresolved tokens.")
            return ""
        return stylesheet

    def state_colors(self) -> Dict[str, QColor]:
        """
        Return the document-tree state colors for the current theme as
        {state_name: QColor}. Falls back to DEFAULT_STATE_COLORS for any
        missing key (so a partial state_colors section is still safe).
        """
        merged: Dict[str, str] = dict(DEFAULT_STATE_COLORS)

        if self._current_theme is not None:
            merged.update(self._current_theme.manifest.state_colors)

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

    def tokens(self) -> Dict[str, str]:
        """
        Return the flat token namespace of the current theme (colors +
        metrics, merged over defaults). Empty dict if no theme is selected.
        """
        if self._current_theme is None:
            log.error("tokens() called but no theme is selected.")
            return {}
        return self._current_theme.manifest.tokens()

    def token(self, name: str, fallback: str | None = None) -> str | None:
        """
        Return the value of a single token of the current theme, or the
        given fallback if the theme is not selected or the token is unknown.
        """
        value = self.tokens().get(name, None)
        if value is None:
            log.warning(f"Token '{name}' not found in current theme.")
            return fallback
        return value

    def color(self, name: str, fallback: str = "#000000") -> QColor:
        """
        Return a token of the current theme as a QColor. Returns the
        fallback color if the token is unknown or not a valid color.
        """
        raw: str | None = self.token(name, fallback=fallback)
        color = QColor(raw if raw is not None else fallback)
        if not color.isValid():
            log.warning(f"Token '{name}' value '{raw}' is not a valid color.")
            color = QColor(fallback)
        return color

    def metrics(self) -> Dict[str, int | float | str]:
        """
        Return the metrics of the current theme merged over DEFAULT_METRICS.
        Empty dict if no theme is selected.
        """
        if self._current_theme is None:
            log.error("metrics() called but no theme is selected.")
            return {}
        return self._current_theme.manifest.merged_metrics()

    def metric(self, name: str, fallback: int = 0) -> int:
        """
        Return a single metric of the current theme as int. Returns the
        fallback if the metric is unknown or not numeric.
        """
        value = self.metrics().get(name, None)
        if value is None:
            log.warning(f"Metric '{name}' not found in current theme.")
            return fallback
        try:
            return int(value)
        except (TypeError, ValueError):
            log.warning(f"Metric '{name}' value '{value}' is not numeric.")
            return fallback

    def build_palette(self) -> "QPalette | None":
        """
        Build a QPalette from the current theme's manifest "palette" section.
        Returns None when no explicit palette is defined. The Qt color scheme
        can still affect the platform palette independently of this section.
        """
        if self._current_theme is None:
            log.error("build_palette() called but no theme is selected.")
            return None
        return self._current_theme.manifest.build_palette()

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

    def qt_color_scheme(self) -> "Qt.ColorScheme":
        """
        Resolve the current theme's color_scheme to a Qt.ColorScheme enum.
        Returns Qt.ColorScheme.Unknown when the heuristic could not infer
        a scheme — the caller should not request a color-scheme change.
        """
        if self._current_theme is None or self._current_theme.color_scheme is None:
            return Qt.ColorScheme.Unknown

        scheme = self._current_theme.color_scheme
        if scheme == "light":
            return Qt.ColorScheme.Light
        if scheme == "dark":
            return Qt.ColorScheme.Dark
        return Qt.ColorScheme.Unknown

    @property
    def baseline_theme(self) -> ThemeMetadata:
        """
        The canonical baseline theme — the one that ships every visual
        asset and that other themes are deltas of. Resolved by looking
        up DEFAULT_THEME_KEY ("light") in the discovered themes; returns
        None if the baseline is somehow missing.
        """
        return self._available_themes.get(DEFAULT_THEME_KEY)

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
