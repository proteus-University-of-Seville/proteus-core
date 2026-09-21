# ==========================================================================
# File: test_language_config.py
# Description: pytest file for the PROTEUS language directory resolution
#              helper (shared by Translator and ProfileSettings)
# Date: 21/09/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.language_config import (
    resolve_language_directory,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _build_languages_config(
    tmp_path: Path, default: str, languages: dict, create_dirs: bool = True
) -> Path:
    """
    Builds a 'languages.xml' file (plus its declared language directories)
    under 'tmp_path' and returns the path to the configuration file.

    :param languages: dict mapping language key -> directory name.
    """
    entries = "\n".join(
        f'    <language key="{key}" path="{path}" />'
        for key, path in languages.items()
    )
    (tmp_path / "languages.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<languages default="{default}">\n{entries}\n</languages>',
        encoding="utf-8",
    )

    if create_dirs:
        for path in languages.values():
            (tmp_path / path).mkdir(parents=True, exist_ok=True)

    return tmp_path / "languages.xml"


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


def test_resolve_language_directory_missing_config_file(tmp_path: Path):
    """
    Check that None is returned when the languages.xml file does not exist.
    """
    result = resolve_language_directory(tmp_path / "languages.xml", "es_ES")
    assert result is None, f"Expected: None, Actual: {result}"


def test_resolve_language_directory_exact_match(tmp_path: Path):
    """
    Check that the directory declared for the requested language is
    returned when it exists.
    """
    config_file = _build_languages_config(
        tmp_path, default="en_us", languages={"en_US": "en_us", "es_ES": "es_es"}
    )

    result = resolve_language_directory(config_file, "es_ES")

    assert result == tmp_path / "es_es", f"Expected: {tmp_path / 'es_es'}, Actual: {result}"


def test_resolve_language_directory_case_insensitive_match(tmp_path: Path):
    """
    Check that the language key lookup is case insensitive.
    """
    config_file = _build_languages_config(
        tmp_path, default="en_us", languages={"en_US": "en_us", "es_ES": "es_es"}
    )

    result = resolve_language_directory(config_file, "es_es")

    assert result == tmp_path / "es_es", f"Expected: {tmp_path / 'es_es'}, Actual: {result}"


def test_resolve_language_directory_fallback_to_default(tmp_path: Path):
    """
    Check that the default language directory is returned when the
    requested language is not declared.
    """
    config_file = _build_languages_config(
        tmp_path, default="en_us", languages={"en_US": "en_us", "es_ES": "es_es"}
    )

    result = resolve_language_directory(config_file, "fr_FR")

    assert result == tmp_path / "en_us", f"Expected: {tmp_path / 'en_us'}, Actual: {result}"


def test_resolve_language_directory_none_language_uses_default(tmp_path: Path):
    """
    Check that the default language directory is returned when no language
    is requested (None).
    """
    config_file = _build_languages_config(
        tmp_path, default="en_us", languages={"en_US": "en_us", "es_ES": "es_es"}
    )

    result = resolve_language_directory(config_file, None)

    assert result == tmp_path / "en_us", f"Expected: {tmp_path / 'en_us'}, Actual: {result}"


def test_resolve_language_directory_declared_but_missing_directory(tmp_path: Path):
    """
    Check that the default language is used when the requested language is
    declared but its directory does not exist on disk.
    """
    config_file = _build_languages_config(
        tmp_path,
        default="en_us",
        languages={"en_US": "en_us", "es_ES": "es_es"},
        create_dirs=False,
    )
    (tmp_path / "en_us").mkdir()
    # es_es directory intentionally not created

    result = resolve_language_directory(config_file, "es_ES")

    assert result == tmp_path / "en_us", f"Expected: {tmp_path / 'en_us'}, Actual: {result}"


def test_resolve_language_directory_unresolvable(tmp_path: Path):
    """
    Check that None is returned when neither the requested language nor the
    default language can be resolved to an existing directory.
    """
    config_file = _build_languages_config(
        tmp_path,
        default="missing_default",
        languages={"fr_FR": "missing_fr"},
        create_dirs=False,
    )

    result = resolve_language_directory(config_file, "es_ES")

    assert result is None, f"Expected: None, Actual: {result}"
