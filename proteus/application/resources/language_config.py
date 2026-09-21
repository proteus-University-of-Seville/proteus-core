# ==========================================================================
# File: language_config.py
# Description: Shared helper to resolve per-language subdirectories that
#              follow PROTEUS' 'languages.xml' convention.
# Date: 21/09/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================
# This convention was introduced by the i18n directories (profile and app
# level) and is reused by the archetype repository so that a profile can
# ship one archetype set per language, mirroring how UI translations are
# already organized.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from lxml import etree as ET

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

LANGUAGE_CONFIG_FILE = "languages.xml"


# --------------------------------------------------------------------------
# Function: resolve_language_directory
# Description: Resolves the subdirectory for a given language declared in a
#              'languages.xml' file.
# Date: 21/09/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
def resolve_language_directory(
    languages_config_file: Path, language: Optional[str]
) -> Optional[Path]:
    """
    Reads a 'languages.xml' configuration file and resolves the directory
    declared for the given language. If the language is not declared (or
    'language' is None), the directory declared as the 'default' language is
    used instead.

    'languages.xml' format:

        <languages default="en_us">
            <language key="en_US" path="en_us" />
            <language key="es_ES" path="es_es" />
        </languages>

    :param languages_config_file: Path to the 'languages.xml' file.
    :param language: Language code to look for (e.g. 'es_ES'), or None to
        resolve the default language directly.

    :return: The resolved directory, or None if the configuration file does
        not exist or no directory could be resolved (neither the requested
        language nor the default language are valid/existing).
    """
    if not languages_config_file.exists():
        log.error(f"Language configuration file not found: {languages_config_file}")
        return None

    languages_tree: ET._ElementTree = ET.parse(languages_config_file)
    languages_root: ET._Element = languages_tree.getroot()

    default_language_directory: str = languages_root.get("default")

    # Look for the requested language, if any
    if language is not None:
        for language_element in languages_root:
            if language_element.get("key", "").lower() == language.lower():
                language_directory: str = language_element.get("path")
                if language_directory is not None:
                    language_directory_path: Path = (
                        languages_config_file.parent / language_directory
                    )
                    if language_directory_path.exists():
                        return language_directory_path
                break

    # Fall back to the default language declared in the configuration file
    if default_language_directory is not None:
        default_language_directory_path: Path = (
            languages_config_file.parent / default_language_directory
        )
        if default_language_directory_path.exists():
            return default_language_directory_path

    return None
