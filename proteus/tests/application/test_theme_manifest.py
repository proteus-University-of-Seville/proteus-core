# ==========================================================================
# File: test_theme_manifest.py
# Description: pytest file for the PROTEUS theme manifest (theme.json)
#              parsing and QSS template rendering.
# Date: 12/09/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtGui import QPalette

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.themes.manifest import (
    ThemeManifest,
    DEFAULT_COLORS,
    DEFAULT_METRICS,
    render_qss,
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def manifest_dir(tmp_path: Path) -> Path:
    """
    Helper fixture that returns a function to write a theme.json file with
    the given content inside a temporary directory.
    """
    return tmp_path


def _write_manifest(directory: Path, content: str) -> Path:
    manifest_path = directory / "theme.json"
    manifest_path.write_text(content, encoding="utf-8")
    return manifest_path


# --------------------------------------------------------------------------
# Parsing tests: happy path
# --------------------------------------------------------------------------
def test_load_valid_manifest(manifest_dir: Path):
    """
    A complete, valid theme.json is parsed into a ThemeManifest with all
    sections populated.
    """
    manifest_path = _write_manifest(
        manifest_dir,
        """{
            "name": "Test Theme",
            "color_scheme": "dark",
            "colors": {"error": "#ff0000", "window": "#000000"},
            "metrics": {"icon_size_button": 24, "custom": "1.5em"},
            "state_colors": {"fresh": "#00ff00"},
            "palette": {"window": "@window", "highlight": "#0080ff"}
        }""",
    )

    manifest = ThemeManifest.load(manifest_path)

    assert manifest is not None
    assert manifest.name == "Test Theme"
    assert manifest.color_scheme == "dark"
    assert manifest.colors == {"error": "#ff0000", "window": "#000000"}
    assert manifest.metrics == {"icon_size_button": 24, "custom": "1.5em"}
    assert manifest.state_colors == {"fresh": "#00ff00"}
    assert manifest.palette == {"window": "@window", "highlight": "#0080ff"}


def test_load_minimal_manifest(manifest_dir: Path):
    """
    An empty JSON object is a valid manifest; every section falls back to
    defaults on access.
    """
    manifest_path = _write_manifest(manifest_dir, "{}")

    manifest = ThemeManifest.load(manifest_path)

    assert manifest is not None
    assert manifest.name is None
    assert manifest.color_scheme is None
    assert manifest.colors == {}
    assert manifest.tokens()["error"] == DEFAULT_COLORS["error"]
    assert manifest.merged_metrics()["icon_size_button"] == DEFAULT_METRICS["icon_size_button"]


def test_load_unknown_top_level_key_is_ignored(manifest_dir: Path):
    """
    Unknown top-level keys do not prevent loading (forward compatibility).
    """
    manifest_path = _write_manifest(
        manifest_dir, '{"name": "X", "future_key": {"a": 1}}'
    )

    manifest = ThemeManifest.load(manifest_path)

    assert manifest is not None
    assert manifest.name == "X"


# --------------------------------------------------------------------------
# Parsing tests: failure modes
# --------------------------------------------------------------------------
def test_load_missing_file_returns_none(manifest_dir: Path):
    manifest = ThemeManifest.load(manifest_dir / "theme.json")
    assert manifest is None


def test_load_malformed_json_returns_none(manifest_dir: Path):
    manifest_path = _write_manifest(manifest_dir, "{not json]")
    assert ThemeManifest.load(manifest_path) is None


def test_load_non_object_top_level_returns_none(manifest_dir: Path):
    manifest_path = _write_manifest(manifest_dir, '["just", "a", "list"]')
    assert ThemeManifest.load(manifest_path) is None


def test_load_invalid_section_types_are_skipped(manifest_dir: Path):
    """
    Sections that are not objects, and entries with wrong value types, are
    skipped without failing the whole manifest.
    """
    manifest_path = _write_manifest(
        manifest_dir,
        """{
            "colors": ["not", "an", "object"],
            "metrics": {"good": 24, "bad": [1, 2]},
            "state_colors": {"fresh": 123},
            "palette": "nope"
        }""",
    )

    manifest = ThemeManifest.load(manifest_path)

    assert manifest is not None
    assert manifest.colors == {}
    assert manifest.metrics == {"good": 24}
    assert manifest.state_colors == {}
    assert manifest.palette == {}


# --------------------------------------------------------------------------
# Token namespace tests
# --------------------------------------------------------------------------
def test_tokens_merge_theme_over_defaults(manifest_dir: Path):
    """
    Theme-defined tokens override defaults; undefined tokens resolve to
    defaults; metrics are stringified into the namespace; state colors are
    NOT part of the QSS token namespace.
    """
    manifest_path = _write_manifest(
        manifest_dir,
        '{"colors": {"error": "#123456"}, "metrics": {"icon_size_tab": 20}}',
    )
    manifest = ThemeManifest.load(manifest_path)

    tokens = manifest.tokens()

    assert tokens["error"] == "#123456"                       # theme override
    assert tokens["window"] == DEFAULT_COLORS["window"]       # default fallback
    assert tokens["icon_size_tab"] == "20"                    # stringified metric
    assert "fresh" not in tokens                              # state colors excluded


# --------------------------------------------------------------------------
# render_qss tests
# --------------------------------------------------------------------------
def test_render_qss_substitutes_tokens():
    template = "QLabel { color: @error; border: 1px solid @border; }"
    tokens = {"error": "red", "border": "gainsboro"}

    rendered = render_qss(template, tokens)

    assert rendered == "QLabel { color: red; border: 1px solid gainsboro; }"


def test_render_qss_leaves_unresolved_tokens():
    """
    An unknown token stays literal in the output (loud failure instead of
    silently wrong styling).
    """
    template = "QLabel { color: @does_not_exist; }"

    rendered = render_qss(template, {})

    assert rendered == template


def test_render_qss_does_not_touch_similar_patterns():
    """
    Tokens require a leading letter/underscore: '@1...' and a bare '@' are
    never substituted. A word preceded by '@' IS a token candidate and the
    whole placeholder (including '@') is replaced when defined — so literal
    '@word' sequences must never appear in templates (e.g. in comments).
    """
    template = "X { a: @1notatoken; b: @; c: email@example.com; }"

    rendered = render_qss(template, {"notatoken": "y", "example": "z"})

    assert rendered == "X { a: @1notatoken; b: @; c: emailz.com; }"


# --------------------------------------------------------------------------
# build_palette tests
# --------------------------------------------------------------------------
def test_build_palette_none_when_no_section(manifest_dir: Path):
    manifest_path = _write_manifest(manifest_dir, "{}")
    manifest = ThemeManifest.load(manifest_path)

    assert manifest.build_palette() is None


def test_build_palette_resolves_tokens_and_literals(manifest_dir: Path):
    manifest_path = _write_manifest(
        manifest_dir,
        """{
            "colors": {"window": "#112233"},
            "palette": {"window": "@window", "highlight": "#0080ff"}
        }""",
    )
    manifest = ThemeManifest.load(manifest_path)

    palette = manifest.build_palette()

    assert palette is not None
    assert palette.color(QPalette.ColorRole.Window).name() == "#112233"
    assert palette.color(QPalette.ColorRole.Highlight).name() == "#0080ff"


def test_build_palette_skips_invalid_entries(manifest_dir: Path):
    """
    Unknown roles, undefined token references and invalid colors are
    skipped; valid entries still apply.
    """
    manifest_path = _write_manifest(
        manifest_dir,
        """{
            "palette": {
                "not_a_role": "#000000",
                "window": "@undefined_token",
                "text": "not-a-color",
                "highlight": "#0080ff"
            }
        }""",
    )
    manifest = ThemeManifest.load(manifest_path)

    palette = manifest.build_palette()

    assert palette is not None
    assert palette.color(QPalette.ColorRole.Highlight).name() == "#0080ff"
