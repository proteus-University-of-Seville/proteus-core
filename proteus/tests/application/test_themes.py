# ==========================================================================
# File: test_themes.py
# Description: pytest file for the PROTEUS themes manager (theme format v2:
#              manifest discovery, token access and template rendering).
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

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_APP_PATH
from proteus.tests import PROTEUS_SAMPLE_DATA_PATH
from proteus.application.resources.themes import Themes
from proteus.application.resources.themes.manifest import (
    DEFAULT_COLORS,
    DEFAULT_METRICS,
    TOKEN_PATTERN,
)

# --------------------------------------------------------------------------
# Global variables and constants
# --------------------------------------------------------------------------

REAL_THEMES_DIRECTORY: Path = PROTEUS_APP_PATH / "resources" / "themes"
GOLDEN_QSS_DIRECTORY: Path = PROTEUS_SAMPLE_DATA_PATH / "themes" / "golden"


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def themes_object() -> Generator[Themes, None, None]:
    """
    Themes is defined as a singleton, it is necessary to 'reset' the object
    before and after each test to ensure that the tests are independent when
    executed in a batch.
    """
    Themes._instances.pop(Themes, None)
    yield Themes()
    Themes._instances.pop(Themes, None)


@pytest.fixture
def loaded_themes(themes_object: Themes) -> Themes:
    """
    Themes singleton with the real application themes directory loaded and
    the default theme selected.
    """
    assert themes_object.load_themes(REAL_THEMES_DIRECTORY)
    themes_object.select_theme("light")
    return themes_object


def _make_theme(theme_dir: Path, with_manifest: bool = True) -> None:
    """
    Helper to create a minimal theme directory in a tmp path.
    """
    theme_dir.mkdir(parents=True)
    (theme_dir / "theme.qss").write_text("QLabel { color: @error; }", encoding="utf-8")
    if with_manifest:
        (theme_dir / "theme.json").write_text(
            '{"colors": {"error": "#aa0000"}}', encoding="utf-8"
        )


# --------------------------------------------------------------------------
# Discovery tests
# --------------------------------------------------------------------------
def test_discovery_finds_shipped_themes(themes_object: Themes):
    """
    The real themes directory yields at least the shipped light and dark
    themes, with manifests parsed.
    """
    assert themes_object.load_themes(REAL_THEMES_DIRECTORY)

    available = themes_object.available_themes
    assert "light" in available
    assert "dark" in available
    assert available["light"].manifest is not None
    assert available["light"].manifest.state_colors.get("fresh") != ""


def test_discovery_requires_manifest(themes_object: Themes, tmp_path: Path):
    """
    Hard switch to format v2: a theme directory with theme.qss but no
    theme.json is skipped.
    """
    _make_theme(tmp_path / "legacy-theme", with_manifest=False)
    _make_theme(tmp_path / "valid-theme", with_manifest=True)

    assert themes_object.load_themes(tmp_path)

    available = themes_object.available_themes
    assert "valid-theme" in available
    assert "legacy-theme" not in available


def test_discovery_requires_qss_template(themes_object: Themes, tmp_path: Path):
    """
    A directory with theme.json but no theme.qss is not a theme.
    """
    theme_dir = tmp_path / "no-qss-theme"
    theme_dir.mkdir()
    (theme_dir / "theme.json").write_text("{}", encoding="utf-8")

    assert not themes_object.load_themes(tmp_path)


def test_discovery_invalid_manifest_is_skipped(themes_object: Themes, tmp_path: Path):
    """
    A theme whose manifest is malformed is skipped; valid themes still load.
    """
    _make_theme(tmp_path / "valid-theme", with_manifest=True)

    broken_dir = tmp_path / "broken-theme"
    broken_dir.mkdir()
    (broken_dir / "theme.qss").write_text("", encoding="utf-8")
    (broken_dir / "theme.json").write_text("{broken", encoding="utf-8")

    assert themes_object.load_themes(tmp_path)
    assert "broken-theme" not in themes_object.available_themes


# --------------------------------------------------------------------------
# Manifest metadata tests
# --------------------------------------------------------------------------
def test_manifest_metadata_overrides_folder_derivation(themes_object: Themes, tmp_path: Path):
    """
    name/color_scheme come from the manifest, not from the folder name.
    """
    theme_dir = tmp_path / "some-folder-name"
    theme_dir.mkdir()
    (theme_dir / "theme.qss").write_text("", encoding="utf-8")
    (theme_dir / "theme.json").write_text(
        '{"name": "Pretty Name", "color_scheme": "dark"}', encoding="utf-8"
    )

    assert themes_object.load_themes(tmp_path)
    metadata = themes_object.available_themes["some-folder-name"]
    assert metadata.name == "Pretty Name"
    assert metadata.color_scheme == "dark"


# --------------------------------------------------------------------------
# Selection tests
# --------------------------------------------------------------------------
def test_select_theme_fallbacks(themes_object: Themes, tmp_path: Path):
    """
    Selection falls back to the first available theme when the requested
    key is unknown and the hardcoded default is absent.
    """
    _make_theme(tmp_path / "aaa-theme", with_manifest=True)

    themes_object.load_themes(tmp_path)
    metadata = themes_object.select_theme("does-not-exist")

    assert metadata is not None
    assert metadata.key == "aaa-theme"


# --------------------------------------------------------------------------
# Token / metric / state color access tests
# --------------------------------------------------------------------------
def test_token_access(loaded_themes: Themes):
    assert loaded_themes.token("error") == "red"
    assert loaded_themes.color("error").name() == "#ff0000"
    assert loaded_themes.token("unknown-token", fallback="fb") == "fb"


def test_metric_access(loaded_themes: Themes):
    assert loaded_themes.metric("icon_size_button") == 32
    assert loaded_themes.metric("unknown-metric", fallback=7) == 7


def test_state_colors_come_from_manifest(loaded_themes: Themes):
    """
    Dark theme state colors defined in theme.json are returned; missing
    keys fall back to defaults.
    """
    loaded_themes.select_theme("dark")
    state_colors = loaded_themes.state_colors()

    assert state_colors["fresh"].name() == "#7fe07f"
    assert state_colors["clean"].name() == "#e6e6e6"


# --------------------------------------------------------------------------
# Stylesheet rendering tests
# --------------------------------------------------------------------------
def test_stylesheet_has_no_unresolved_tokens(loaded_themes: Themes):
    loaded_themes.select_theme("dark")
    stylesheet = loaded_themes.stylesheet()

    assert stylesheet != ""
    assert TOKEN_PATTERN.search(stylesheet) is None


def test_rendered_stylesheet_reacts_to_token_values(themes_object: Themes, tmp_path: Path):
    """
    Changing a token value in theme.json changes the rendered stylesheet.
    """
    _make_theme(tmp_path / "token-theme", with_manifest=True)

    themes_object.load_themes(tmp_path)
    themes_object.select_theme("token-theme")

    assert "color: #aa0000;" in themes_object.stylesheet()


# --------------------------------------------------------------------------
# Golden-master parity tests (format v1 -> v2 regression)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("theme_key", ["light", "dark"])
def test_rendered_stylesheet_matches_v1_golden(loaded_themes: Themes, theme_key: str):
    """
    The v2 migration must be visually lossless: rendering the migrated
    theme.qss template with the theme.json tokens must reproduce the
    baseline QSS (with normalized indentation) byte for byte.
    """
    golden_path = GOLDEN_QSS_DIRECTORY / f"{theme_key}.qss"
    golden = golden_path.read_text(encoding="utf-8")

    loaded_themes.select_theme(theme_key)
    rendered = loaded_themes.stylesheet()

    assert rendered == golden
