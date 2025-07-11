# ==========================================================================
# File: translator.py
# Description: Manage the language translations for PROTEUS application
# Date: 26/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict, List
from pathlib import Path
import yaml
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from lxml import etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

LANGUAGE_CONFIG_FILE = "languages.xml"


# --------------------------------------------------------------------------
# Class: Translator
# Description: Manage the language translations for PROTEUS application
# Date: 26/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
# TODO: Consider allowing external i18n directories to load languages to
# available languages. This will allow Proteus profiles to add new languages.
class Translator(metaclass=SingletonMeta):
    """
    Manage the language translations for PROTEUS application. It stores the
    current language translations. It can be only one instance of this class.
    Provides methods to get the current translation for a given key.

    Translations are stored in i18n directory. Each language has its own
    directory with the translations files or file. The translations files
    are yaml files.

    Available languages are based on the built-in language configuration file
    located in application i18n directory.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Constructor for Translator class.
    # Date: 26/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self):
        """
        Initializes the Translator class.
        """
        # Proteus configuration
        self.current_language: str = None
        self.proteus_i18n_directory: Path = None

        # Properties
        self._available_languages = None

        # Translations variable
        self._translations: Dict[str, str] = {}

    # ==========================================================================
    # Properties
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: get_available_languages
    # Description: Returns the available languages for the application.
    # Date: 01/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @property
    def available_languages(self) -> List[str]:
        """
        Read the application configuration file located in the resources directory
        and returns the available languages for the application.

        Check if the language directory exists before adding it to the list of
        available languages.

        :return: List of available languages for the application. Empty list if
                    no languages are found.
        """
        # Check if the language configuration is set
        assert (
            self.current_language is not None
            and self.proteus_i18n_directory is not None
        ), "Language configuration must be set before loading the translations."

        # If the available languages are already loaded, return them
        if self._available_languages:
            return self._available_languages
        else:
            # Build the path to the language configuration file
            language_config_file: Path = (
                self.proteus_i18n_directory / LANGUAGE_CONFIG_FILE
            )

            # Read the language configuration file
            languages_tree: ET._ElementTree = ET.parse(language_config_file)
            languages_root: ET._Element = languages_tree.getroot()

            # List of available languages
            available_languages: List[str] = []

            # Iterate over the language tags
            for language in languages_root:
                # Get the language code
                language_code: str = language.get("key")

                # Get the language directory
                language_directory: str = language.get("path")

                # Check if the language path exists
                if language_directory is not None:
                    language_directory_path: Path = (
                        self.proteus_i18n_directory / language_directory
                    )
                    if language_directory_path.exists():
                        available_languages.append(language_code)

            # Store the available languages
            self._available_languages = available_languages
            return self._available_languages

    # ==========================================================================
    # Helper methods
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: _read_config_file
    # Description: Reads the language configuration file and returns the path
    #              to the translations directory.
    # Date: 01/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _read_config_file(self, language_config_file: Path) -> Path:
        """
        Reads the language configuration file and return the path to the lagnuage
        directory or file.

        Check if the language configuration file has the language entry for the
        current application language. If not, it returns the default language if
        it exists. If there is no default language or current language is not
        found, it returns None.

        :param language_config_file: Path to the language configuration file.

        :return: Path to the translations directory/file or None if not found any.
        """
        # Check if the language configuration file exists
        if not language_config_file.exists():
            log.error(f"Language configuration file not found: {language_config_file}")
            return None

        # Read the language configuration file
        languages_tree: ET._ElementTree = ET.parse(language_config_file)
        languages_root: ET._Element = languages_tree.getroot()

        # Get the default language directory if exists
        default_language_directory: str = languages_root.get("default")

        # Iterate over the language tags
        for language in languages_root:
            # If the key if the current language
            if language.get("key").lower() == self.current_language.lower():
                log.debug(
                    f"Configuration for language '{self.current_language}' found in file '{language_config_file}'"
                )

                # Get the language directory
                language_directory: str = language.get("path")

                # Check if the language directory exists
                if language_directory is not None:
                    language_directory_path: Path = (
                        language_config_file.parent / language_directory
                    )
                    if language_directory_path.exists():
                        return language_directory_path

        # If the current language is not found, return the default language if exists
        if default_language_directory is not None:
            default_language_directory_path: Path = Path(default_language_directory)
            if default_language_directory_path.exists():
                return default_language_directory_path
        else:
            return None

    # --------------------------------------------------------------------------
    # Method: _load_translations
    # Description: Loads the translations found in the given directory
    # Date: 26/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _load_translations(self, translations_path: Path) -> None:
        """
        Loads the translations files found in the given directory/file. It reads
        the yaml files and stores the translations in the _translations variable.
        Loads both .yaml and .yml files.

        Updates the _translations variable dictionary with the new translations.
        This means it overwrites the translations for the same key if repeated.

        :param translations_path: Path to the translations directory or file.
        """
        log.info(f"Loading translations from: {translations_path.as_posix()}")

        # Check if the translations_path is a directory or a file
        if translations_path.is_dir():
            # Get all the yaml files in the directory
            translations_yaml_files: List[Path] = list(
                translations_path.rglob("*.yaml")
            )
            translations_yml_files: List[Path] = list(translations_path.rglob("*.yml"))
            translations_files: List[Path] = (
                translations_yaml_files + translations_yml_files
            )
        else:
            translations_files = [translations_path]

        # Iterate over the yaml files
        for file in translations_files:
            log.debug(f"Loading translations from file: {file.as_posix()}")

            # Read the yaml file
            with open(file, "r", encoding="utf-8") as f:
                translations: dict = yaml.safe_load(f)

                # Update the translations dictionary
                self._translations.update(translations)

    # ==========================================================================
    # Public methods
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: set_language
    # Description: Set the current language configuration for the application.
    # Date: 07/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_language(self, language: str) -> None:
        """
        Set the current language configuration for the application.
        """
        self.current_language = language

    # --------------------------------------------------------------------------
    # Method: set_proteus_i18n_directory
    # Description: Set the proteus i18n directory for the application.
    # Date: 07/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_proteus_i18n_directory(self, i18n_directory: Path) -> None:
        """
        Set the proteus i18n directory for the application.
        """
        self.proteus_i18n_directory = i18n_directory

    # --------------------------------------------------------------------------
    # Method: load_translations
    # Description: Load the translations for the current language.
    # Date: 07/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def load_translations(self, translations_directory: Path) -> bool:
        """
        Load the translations for the current language based on the
        configuration previously set. Translations are loaded from the
        translations directory provided.

        It reads the language configuration file and loads the translations
        for the current language. If the current language is not found, it
        tries to load the default language if it exists.

        Language configuration must be set before calling this method.

        :param translations_directory: Path to the translations directory.

        :return: True if translations are loaded successfully, False otherwise.
        """
        # Check if the language configuration is set
        assert (
            self.current_language is not None
            and self.proteus_i18n_directory is not None
        ), "Language configuration must be set before loading the translations."

        if translations_directory is None:
            log.error("Translations directory not found.")
            return False
        
        # Load archetype repository translations ----------------
        lang_file: Path = (
            translations_directory / LANGUAGE_CONFIG_FILE
        )
        _translations_directory: Path = self._read_config_file(
            lang_file
        )
        if _translations_directory is not None:
            try:
                self._load_translations(_translations_directory)
                return True
            except Exception as e:
                log.error(
                    f"Error loading translations for language '{self.current_language}' in '{lang_file.as_posix()}' file: {e}"
                )
                return False
        else:
            log.warning(
                f"Language directory not found for language '{self.current_language}' in '{lang_file}' file."
            )
            return False

    # --------------------------------------------------------------------------
    # Method: text
    # Description: Returns the translation for the given key.
    # Date: 02/02/2024
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # NOTE: this method follows a EAFP philosophy since most of the strings
    # in the app will have translations. For really (really) big archetype
    # repositories that are not translated, this might cause a performance
    # issue on app startup. Also tests may be affected by this.
    # Consider implement a LBYL flag/mode for testing purposes.
    def text(self, key: str, *args, alternative_text: str = None, allow_new_line_characters: bool = False) -> str:
        """
        Returns the translation found for the given key. If no translation is
        found, it returns the key or the alternative text if provided.

        If there are arguments, they are formatted in the translation.
        Key is processed to lowercase and replace spaces with underscores.

        :param key: Key to find the translation.
        :param args: Arguments to format the translation.
        :param alternative_text: Text to return if no translation is found.

        :return: Translation for the given key or the key itself if not found.
                    If alternative_text is provided and no translation is found,
                    it returns the alternative text.
        """
        # Check type of key
        assert isinstance(key, str), f"Language code key must be string type '{key}'"

        # Preprocess the key
        text_code: str = key.lower().replace(" ", "_")

        # Get the translation for the given key
        translation: str = ""
        try:
            translation = self._translations[text_code]
        except KeyError:
            # If translation not found return the key itself or the alternative text
            if alternative_text is not None:
                translation = alternative_text
            else:
                translation = key
            log.warning(
                f"Text not found for code '{text_code}' in '{self.current_language}' file."
            )

        # Check if there are arguments to format the translation
        if args:
            translation = translation.format(*args)

        # Check if new line characters are allowed
        if not allow_new_line_characters:
            translation = translation.replace("\n", " ")

        return translation


# --------------------------------------------------------------------------
# Function: translate
# Description: Returns the translation for the given key.
# Date: 17/05/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
def translate(key: str, *args, alternative_text: str = None, allow_new_line_characters: bool = False) -> str:
        """
        Returns the translation found for the given key. If no translation is
        found, it returns the key or the alternative text if provided.

        If there are arguments, they are formatted in the translation.
        Key is processed to lowercase and replace spaces with underscores.

        :param key: Key to find the translation.
        :param args: Arguments to format the translation.
        :param alternative_text: Text to return if no translation is found.
        :param allow_new_line_characters: Flag to allow new line characters in the translation.

        :return: Translation for the given key or the key itself if not found.
                    If alternative_text is provided and no translation is found,
                    it returns the alternative text.
        """

        return Translator().text(key, *args, alternative_text=alternative_text, allow_new_line_characters=allow_new_line_characters)