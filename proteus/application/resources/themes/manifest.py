# ==========================================================================
# File: manifest.py
# Description: Theme manifest (theme.json) model, parsing and QSS template
#              rendering for the PROTEUS theming engine.
# Date: 12/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================
# THEME FORMAT (v2)
# -----------------
# A theme is a directory containing:
#   - theme.json      manifest (this module)
#   - theme.qss       QSS template with @token placeholders
#   - icons/          optional icon delta (icons.xml + assets)
#
# theme.json schema:
#   {
#     "name":         "Light",            (optional, derived from folder if absent)
#     "color_scheme": "light" | "dark",   (optional, derived from folder if absent)
#     "colors":       { "<token>": "<css-color>", ... },
#     "metrics":      { "<token>": <int|float|string>, ... },
#     "state_colors": { "fresh"|"dirty"|"dead"|"clean": "<css-color>", ... },
#     "palette":      { "<palette-role>": "<css-color|@token>", ... }   (optional)
#   }
#
# Tokens from "colors" and "metrics" are substituted into the theme.qss
# template by render_qss() as @token. Every token resolves against the
# theme's own values merged over DEFAULT_COLORS / DEFAULT_METRICS, so a
# theme only overrides what it needs. An unresolved token is left as-is in
# the output and logged as an error (loud failure beats silent wrong colors).
#
# "state_colors" are consumed by Python code (document tree brushes), not by
# the QSS template. "palette" optionally sets explicit QPalette roles;
# color_scheme is a separate Qt style hint.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QColor, QPalette

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

THEME_MANIFEST_FILE: str = "theme.json"

# Token placeholder syntax in QSS templates: @token_name
TOKEN_PATTERN = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)")

# Top-level keys allowed in theme.json. Unknown keys are warned about and
# ignored, keeping forward compatibility with future schema additions.
_MANIFEST_KNOWN_KEYS = {
    "name",
    "color_scheme",
    "colors",
    "metrics",
    "state_colors",
    "palette",
}

# --------------------------------------------------------------------------
# Default token values (T1: token taxonomy)
# --------------------------------------------------------------------------
# Fallback values used when a theme does not define a token that its QSS
# template references. Values mirror the baseline "light" theme; tokens not
# used by the light template get neutral light-safe values.
DEFAULT_COLORS: Dict[str, str] = {
    # Feedback ----------------------------------------------------------
    "error": "red",
    "spellcheck_error": "#ff0000",
    # Text --------------------------------------------------------------
    "text": "black",
    "text_muted": "black",
    "disabled_text": "#888888",
    # Selection / interaction -------------------------------------------
    "selection_bg": "lightcyan",
    "selection_text": "black",
    "hover_bg": "azure",
    "hover_border": "skyblue",
    "hover_text": "black",
    "pressed_bg": "lightcyan",
    # Borders -------------------------------------------------------------
    "border": "gainsboro",
    "border_subtle": "#e1e1e1",
    "border_strong": "slategray",
    # Surfaces ------------------------------------------------------------
    "window": "#ffffff",
    "alternate_base": "#f5f5f5",
    "button_surface": "white",
    "input_surface": "white",
    "header_surface": "#f3f3f3",
    "tooltip_surface": "white",
    "tab_surface": "#f9f9f9",
    "tab_surface_inactive": "#ececec",
    "tab_surface_selected": "#f9f9f9",
    "chrome_surface": "#f9f9f9",
    "statusbar_surface": "#ffe7e7e7",
    "splitter_surface": "#f1f1f1",
    "scrollbar_handle": "#c0c0c0",
    "scrollbar_handle_hover": "#a0a0a0",
    # Disabled ------------------------------------------------------------
    "disabled_bg": "#f3f3f3",
    "wizard_disabled_bg": "#ffffff",
    # Calendar (legacy blue, shared by shipped themes) --------------------
    "calendar_accent": "#0080ff",
    "calendar_hover": "#004589",
    "calendar_pressed": "#89c4ff",
    "calendar_text": "white",
}

# Metric tokens consumed by Python code (icon sizes, minimum widths, ...).
# They are also available to QSS templates (substituted as plain numbers).
DEFAULT_METRICS: Dict[str, int] = {
    "icon_size_button": 32,
    "icon_size_tab": 32,
    "icon_size_tree": 22,
    "icon_size_statusbar": 16,
    "profile_icon_height": 32,
    "tree_min_width": 200,
    "views_min_width": 400,
}

# Document-tree state colors (consumed by Python code, not by QSS
# templates). Merged under each theme's manifest "state_colors" section.
DEFAULT_STATE_COLORS: Dict[str, str] = {
    "fresh": "#006400",
    "dirty": "#B8860B",
    "dead":  "#8B0000",
    "clean": "#000000",
}

# QPalette roles that may be set from the manifest "palette" section.
# Keys are lower_snake_case role names; values may reference color tokens
# with "@token" or be literal CSS colors.
PALETTE_ROLES: Dict[str, QPalette.ColorRole] = {
    "window": QPalette.ColorRole.Window,
    "window_text": QPalette.ColorRole.WindowText,
    "base": QPalette.ColorRole.Base,
    "alternate_base": QPalette.ColorRole.AlternateBase,
    "text": QPalette.ColorRole.Text,
    "button": QPalette.ColorRole.Button,
    "button_text": QPalette.ColorRole.ButtonText,
    "highlight": QPalette.ColorRole.Highlight,
    "highlighted_text": QPalette.ColorRole.HighlightedText,
    "link": QPalette.ColorRole.Link,
    "placeholder_text": QPalette.ColorRole.PlaceholderText,
    "tool_tip_base": QPalette.ColorRole.ToolTipBase,
    "tool_tip_text": QPalette.ColorRole.ToolTipText,
    "bright_text": QPalette.ColorRole.BrightText,
}


def render_qss(template: str, tokens: Dict[str, str]) -> str:
    """
    Substitute every ``@token`` placeholder in the template with its value
    from the tokens dict. Unresolved tokens are left as-is in the output and
    logged as errors so authoring mistakes are visible instead of silently
    producing wrong styles.

    :param template: QSS template content.
    :param tokens: Token name to value mapping (already merged over defaults).
    :return: Rendered QSS string.
    """

    def _substitute(match: re.Match) -> str:
        token_name: str = match.group(1)
        if token_name in tokens:
            return str(tokens[token_name])
        log.error(
            f"Unresolved token '@{token_name}' in QSS template. "
            "Define it in theme.json or in DEFAULT_COLORS/DEFAULT_METRICS."
        )
        return match.group(0)

    return TOKEN_PATTERN.sub(_substitute, template)


@dataclass
class ThemeManifest:
    """
    In-memory representation of theme.json. Colors, metrics and state colors
    have defaults; palette roles are applied only when explicitly specified.
    """

    name: str | None = None
    color_scheme: str | None = None
    colors: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, int | float | str] = field(default_factory=dict)
    state_colors: Dict[str, str] = field(default_factory=dict)
    palette: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, manifest_path: Path) -> "ThemeManifest | None":
        """
        Parse and validate a theme.json file. Returns None (logging the
        reason) when the file is missing, unreadable, malformed JSON or its
        top-level value is not an object. Unknown top-level keys and invalid
        section entries are logged as warnings and skipped.

        :param manifest_path: Path to the theme.json file.
        :return: ThemeManifest instance or None on hard failure.
        """
        if not manifest_path.exists():
            log.error(f"Theme manifest '{manifest_path}' does not exist.")
            return None

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"Error parsing theme manifest '{manifest_path}': {e}")
            return None

        if not isinstance(raw, dict):
            log.error(
                f"Theme manifest '{manifest_path}' must contain a JSON object, "
                f"got {type(raw).__name__}."
            )
            return None

        # Unknown keys are ignored to allow future manifest extensions.
        for key in raw:
            if key not in _MANIFEST_KNOWN_KEYS:
                log.warning(
                    f"Unknown key '{key}' in theme manifest '{manifest_path}'. "
                    f"Known keys: {sorted(_MANIFEST_KNOWN_KEYS)}. Ignoring it."
                )

        name = raw.get("name")
        if name is not None and not isinstance(name, str):
            log.warning(f"Invalid 'name' in '{manifest_path}', ignoring it.")
            name = None

        color_scheme = raw.get("color_scheme")
        if color_scheme is not None and not isinstance(color_scheme, str):
            log.warning(f"Invalid 'color_scheme' in '{manifest_path}', ignoring it.")
            color_scheme = None

        colors = cls._parse_str_section(raw, "colors", manifest_path)
        metrics = cls._parse_metrics_section(raw, manifest_path)
        state_colors = cls._parse_str_section(raw, "state_colors", manifest_path)
        palette = cls._parse_str_section(raw, "palette", manifest_path)

        return cls(
            name=name,
            color_scheme=color_scheme,
            colors=colors,
            metrics=metrics,
            state_colors=state_colors,
            palette=palette,
        )

    @staticmethod
    def _parse_str_section(
        raw: dict, section: str, manifest_path: Path
    ) -> Dict[str, str]:
        """
        Parse a manifest section whose values must be strings. Invalid
        entries are warned about and skipped.
        """
        value = raw.get(section, {})
        if not isinstance(value, dict):
            log.warning(
                f"Section '{section}' in '{manifest_path}' must be an object, "
                "ignoring it."
            )
            return {}

        result: Dict[str, str] = {}
        for k, v in value.items():
            if isinstance(k, str) and isinstance(v, str):
                result[k] = v
            else:
                log.warning(
                    f"Invalid entry '{k}': '{v}' in section '{section}' of "
                    f"'{manifest_path}', values must be strings. Skipping it."
                )
        return result

    @staticmethod
    def _parse_metrics_section(
        raw: dict, manifest_path: Path
    ) -> Dict[str, int | float | str]:
        """
        Parse the 'metrics' section, accepting int, float and string values.
        Invalid entries are warned about and skipped.
        """
        value = raw.get("metrics", {})
        if not isinstance(value, dict):
            log.warning(
                f"Section 'metrics' in '{manifest_path}' must be an object, "
                "ignoring it."
            )
            return {}

        result: Dict[str, int | float | str] = {}
        for k, v in value.items():
            if isinstance(k, str) and isinstance(v, (int, float, str)):
                result[k] = v
            else:
                log.warning(
                    f"Invalid metric '{k}': '{v}' in '{manifest_path}', values "
                    "must be int, float or string. Skipping it."
                )
        return result

    def tokens(self) -> Dict[str, str]:
        """
        Return the flat token namespace used for QSS rendering: colors merged
        over DEFAULT_COLORS plus metrics over DEFAULT_METRICS (stringified).
        State colors are NOT included (consumed by Python code only).
        """
        merged_colors: Dict[str, str] = {**DEFAULT_COLORS, **self.colors}
        merged_metrics = {**DEFAULT_METRICS, **self.metrics}
        return {**merged_colors, **{k: str(v) for k, v in merged_metrics.items()}}

    def merged_metrics(self) -> Dict[str, int | float | str]:
        """Return the theme metrics merged over DEFAULT_METRICS."""
        return {**DEFAULT_METRICS, **self.metrics}

    def build_palette(self) -> "QPalette | None":
        """
        Build a QPalette from the manifest "palette" section. Values may be
        literal CSS colors or references to color tokens ("@token").

        Returns None when the theme defines no explicit palette mapping.
        """
        if not self.palette:
            return None

        color_tokens: Dict[str, str] = {**DEFAULT_COLORS, **self.colors}
        palette = QPalette()

        for role_key, raw_value in self.palette.items():
            role = PALETTE_ROLES.get(role_key)
            if role is None:
                log.warning(
                    f"Unknown palette role '{role_key}' in theme manifest. "
                    f"Known roles: {sorted(PALETTE_ROLES)}. Skipping it."
                )
                continue

            # Resolve @token references against the color token namespace
            value: str = raw_value
            token_match = TOKEN_PATTERN.fullmatch(raw_value.strip())
            if token_match is not None:
                token_name = token_match.group(1)
                if token_name not in color_tokens:
                    log.warning(
                        f"Palette role '{role_key}' references undefined token "
                        f"'@{token_name}'. Skipping it."
                    )
                    continue
                value = color_tokens[token_name]

            color = QColor(value)
            if not color.isValid():
                log.warning(
                    f"Invalid color '{value}' for palette role '{role_key}'. "
                    "Skipping it."
                )
                continue

            palette.setColor(role, color)

        return palette
