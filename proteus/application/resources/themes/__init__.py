# ==========================================================================
# File: __init__.py
# Description: PROTEUS themes package. Groups the theming engine modules:
#              manifest (theme.json model + QSS template rendering),
#              manager (theme discovery, selection and token access) and
#              service (runtime theme application).
# Date: 13/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================
# ThemeService is exported lazily below to avoid a config -> spellcheck ->
# themes -> service -> config import cycle.
# ==========================================================================

from proteus.application.resources.themes.manifest import (
    ThemeManifest,
    THEME_MANIFEST_FILE,
    DEFAULT_COLORS,
    DEFAULT_METRICS,
    DEFAULT_STATE_COLORS,
    PALETTE_ROLES,
    TOKEN_PATTERN,
    render_qss,
)
from proteus.application.resources.themes.manager import (
    Themes,
    ThemeMetadata,
    THEMES_DIRECTORY,
    DEFAULT_THEME_KEY,
)


def __getattr__(name: str):
    """
    Lazy re-export of ThemeService (PEP 562).

    The service module imports Config, which transitively imports this
    package (config → app_settings → spellcheck → themes). Importing the
    service eagerly at package initialization closes a circular import
    whenever the application is entered config-first. Resolving it lazily
    keeps `from ...themes import ThemeService` working without the cycle.
    """
    if name == "ThemeService":
        from proteus.application.resources.themes.service import ThemeService

        return ThemeService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
