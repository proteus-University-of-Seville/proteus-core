# ==========================================================================
# File: app_settings.py
# Description: PROTEUS app settings module
# Date: 15/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
import shutil
from pathlib import Path
from dataclasses import dataclass, replace
from configparser import ConfigParser

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.spellcheck import SpellCheckerWrapper

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

CONFIG_FILE: str = "proteus.ini"
DEFAULT_CONFIG_FILE: str = "proteus.default.ini"

# Directories (convention)
RESOURCES_DIRECTORY: str = "resources"
ICONS_DIRECTORY: str = "icons"
I18N_DIRECTORY: str = "i18n"
PLUGINS_DIRECTORY: str = "plugins"
PROFILES_DIRECTORY: str = "profiles"

# User editable settings
SETTINGS: str = "settings"
SETTING_LANGUAGE: str = "language"
SETTING_SPELLCHECKER_LANGUAGE: str = "spellchecker_language"
SETTING_DEFAULT_VIEW: str = "default_view"
SETTING_SELECTED_PROFILE: str = "selected_profile"
SETTING_USING_DEFAULT_PROFILE: str = "using_default_profile"
SETTING_CUSTOM_PROFILE_PATH: str = "custom_profile_path"
SETTING_OPEN_PROJECT_ON_STARTUP: str = "open_project_on_startup"
SETTING_EDIT_ON_CLONE: str = "edit_on_clone"
# Special advanced settings
SETTING_XSLT_DEBUG_MODE: str = "xslt_debug_mode"
SETTING_DEVELOPER_FEATURES: str = "developer_features"

# User session data
SESSION: str = "session"
SESSION_LAST_PROJECT_OPENED: str = "last_project_opened"


# logging configuration
log = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """
    Store app settings located in the app configuration file.
    """

    # General purpose variables
    app_path: Path = None
    settings_file_path: Path = None
    config_parser: ConfigParser = None

    # Directory settings (not editable by the user)
    resources_directory: Path = None
    icons_directory: Path = None
    i18n_directory: Path = None
    profiles_directory: Path = None
    plugins_directory: Path = None

    # Application settings (User editable settings)
    language: str = None
    spellchecker_language: str = None
    default_view: str = None
    selected_profile: str = None
    using_default_profile: bool = None
    custom_profile_path: Path = None
    open_project_on_startup: bool = None
    edit_on_clone: bool = False
    # Special advanced settings (not editable by the user)
    # These settings must be set manually in the configuration file
    xslt_debug_mode: bool = False
    developer_features: bool = False

    # --------------------------------------------------------------------------
    # Method: load
    # Description: Load user settings from the configuration file
    # Date: 15/03/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def load(app_path: Path) -> "AppSettings":
        """
        Loads the user/app settings from the configuration file located in the
        execution directory. If the configuration file does not exist, it is
        copied from the default configuration file located in the application
        directory.
        """
        config_file_path: Path = app_path / DEFAULT_CONFIG_FILE

        assert (
            config_file_path.exists()
        ), f"PROTEUS default configuration file '{CONFIG_FILE}' does not exist in '{app_path}'!"

        # Check for proteus.ini file where the application is executed
        # NOTE: This allows to change config in single executable app version
        config_file_exec_path: Path = Path.cwd() / CONFIG_FILE
        if not config_file_exec_path.exists():
            log.warning(
                f"PROTEUS configuration file '{CONFIG_FILE}' does not exist in the execution path. Copying configuration file to execution path..."
            )

            # Copy proteus.ini file to execution path
            shutil.copy(config_file_path, config_file_exec_path)

        try:
            config_parser: ConfigParser = ConfigParser()
            config_parser.read(config_file_exec_path, encoding="utf-8")
        except Exception as e:
            log.error(
                f"Error loading configuration file '{config_file_exec_path}': {e}"
                "Configuration file will be deleted and copied again from the default configuration file."
            )

            # Delete the corrupted configuration file
            config_file_exec_path.unlink()

            # Copy proteus.ini file to execution path
            shutil.copy(config_file_path, config_file_exec_path)

            # Load the configuration file again
            config_parser: ConfigParser = ConfigParser()
            config_parser.read(config_file_exec_path, encoding="utf-8")

        # Variable to store init file path
        # This is required to avoid loosing track if cwd changes
        settings_file_path: Path = config_file_exec_path

        log.info(f"Loading settings from '{settings_file_path}'...")

        app_settings = AppSettings(
            app_path=app_path,
            settings_file_path=settings_file_path,
            config_parser=config_parser,
        )

        app_settings._load_directories()
        app_settings._load_user_settings()

        return app_settings

    # --------------------------------------------------------------------------
    # Method: _load_directories
    # Description: Load directory settings from the configuration file
    # Date: 15/03/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _load_directories(self) -> None:
        """
        Load directory settings from the configuration file. Directories are
        defined by convention and are not editable by the user.
        """
        # Directories section
        self.resources_directory = self.app_path / RESOURCES_DIRECTORY
        self.profiles_directory = self.app_path / PROFILES_DIRECTORY
        self.icons_directory = self.resources_directory / ICONS_DIRECTORY
        self.i18n_directory = self.resources_directory / I18N_DIRECTORY
        self.plugins_directory = self.resources_directory / PLUGINS_DIRECTORY
        
        assert (
            self.resources_directory.exists()
        ), f"PROTEUS resources directory '{self.resources_directory}' does not exist!"
        assert (
            self.icons_directory.exists()
        ), f"PROTEUS icons directory '{self.icons_directory}' does not exist!"
        assert (
            self.i18n_directory.exists()
        ), f"PROTEUS i18n directory '{self.i18n_directory}' does not exist!"
        assert (
            self.profiles_directory.exists()
        ), f"PROTEUS profiles directory '{self.profiles_directory}' does not exist!"
        assert (
            self.plugins_directory.exists()
        ), f"PROTEUS plugins directory '{self.plugins_directory}' does not exist!"

        log.info(f"Directories loaded from '{self.settings_file_path}'.")
        log.info(f"{self.profiles_directory = }")
        log.info(f"{self.resources_directory = }")
        log.info(f"{self.icons_directory = }")
        log.info(f"{self.i18n_directory = }")
        log.info(f"{self.plugins_directory = }")

    # --------------------------------------------------------------------------
    # Method: _load_user_settings
    # Description: Load user editable settings from the configuration file
    # Date: 15/03/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _load_user_settings(self) -> None:
        """
        Load user editable settings from the configuration file.
        """
        # Settings section
        settings = self.config_parser[SETTINGS]

        # Language -----------------------
        self.language = settings[SETTING_LANGUAGE]

        log.info(
            f"Config file '{self.settings_file_path}' | Language: '{self.language}'"
        )

        # Spellchecker language -----------------------
        spellchecker_language = settings[SETTING_SPELLCHECKER_LANGUAGE]

        # Check if the spellchecker language is available
        if spellchecker_language not in SpellCheckerWrapper.list_available_languages():
            log.warning(
                f"Spellchecker language '{spellchecker_language}' is not available. No spellchecker will be used."
            )
            spellchecker_language = None

        self.spellchecker_language = spellchecker_language

        log.info(
            f"Config file '{self.settings_file_path}' | Spellchecker language: '{self.spellchecker_language}'"
        )

        # Default view -------------------
        self.default_view = settings[SETTING_DEFAULT_VIEW]

        log.info(
            f"Config file '{self.settings_file_path}' | Default view: '{self.default_view}'"
        )

        # Profile ------------------------
        self.selected_profile = settings[SETTING_SELECTED_PROFILE]
        self.using_default_profile = settings.getboolean(
            SETTING_USING_DEFAULT_PROFILE, True
        )

        custom_profile_path_str: str = settings[SETTING_CUSTOM_PROFILE_PATH]
        self.custom_profile_path = (
            Path(custom_profile_path_str) if custom_profile_path_str else None
        )

        self._validate_profile_path()

        # Load project on startup ------------------------
        self.open_project_on_startup = settings.getboolean(
            SETTING_OPEN_PROJECT_ON_STARTUP, False
        )

        # Edit on clone ------------------------
        self.edit_on_clone = settings.getboolean(SETTING_EDIT_ON_CLONE, False)

        # XSLT debug mode ------------------------
        self.xslt_debug_mode = settings.getboolean(SETTING_XSLT_DEBUG_MODE, False)

        # Raw model editor ------------------------
        self.developer_features = settings.getboolean(SETTING_DEVELOPER_FEATURES, False)

        log.info(f"Loaded app user settings from '{self.settings_file_path}'.")
        log.info(f"{self.language = }")
        log.info(f"{self.default_view = }")
        log.info(f"{self.selected_profile = }")
        log.info(f"{self.using_default_profile = }")
        log.info(f"{self.custom_profile_path = }")
        log.info(f"{self.open_project_on_startup = }")
        log.info(f"{self.edit_on_clone = }")
        log.info(f"{self.xslt_debug_mode = }")
        log.info(f"{self.developer_features = }")

    # --------------------------------------------------------------------------
    # Method: _validate_profile_path
    # Description: Validate the custom profile path
    # Date: 03/04/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _validate_profile_path(self) -> None:
        """
        Validate the custom profile path changing the using_default_profile flag
        if the custom profile path is not valid.
        """

        if not self.using_default_profile:
            if self.custom_profile_path is None:
                log.error(
                    f"Custom profile path not specified in '{self.settings_file_path}'. Using default profile..."
                )
                self.using_default_profile = True
            elif not self.custom_profile_path.exists():
                log.error(
                    f"Custom profile path '{self.custom_profile_path}' does not exist. Using default profile..."
                )
                self.using_default_profile = True

    # --------------------------------------------------------------------------
    # Method: clone
    # Description: Clone the current object with the new user settings (if any)
    # Date: 18/03/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def clone(
        self,
        language: str = None,
        spellchecker_language: str = None,
        default_view: str = None,
        selected_profile: str = None,
        using_default_profile: bool = None,
        custom_profile_path: Path = None,
        open_project_on_startup: bool = None,
        edit_on_clone: bool = None,
    ) -> "AppSettings":
        """
        Clone the current object with the new user settings (if any).
        """
        if language is None:
            language = self.language

        if spellchecker_language is None:
            spellchecker_language = self.spellchecker_language

        if default_view is None:
            default_view = self.default_view

        if selected_profile is None:
            selected_profile = self.selected_profile

        if using_default_profile is None:
            using_default_profile = self.using_default_profile

        if custom_profile_path is None:
            custom_profile_path = self.custom_profile_path

        if open_project_on_startup is None:
            open_project_on_startup = self.open_project_on_startup

        if edit_on_clone is None:
            edit_on_clone = self.edit_on_clone

        new_settings = replace(
            self,
            language=language,
            spellchecker_language=spellchecker_language,
            default_view=default_view,
            selected_profile=selected_profile,
            using_default_profile=using_default_profile,
            custom_profile_path=custom_profile_path,
            open_project_on_startup=open_project_on_startup,
            edit_on_clone=edit_on_clone,
        )

        new_settings._validate_profile_path()
        return new_settings

    # --------------------------------------------------------------------------
    # Method: save
    # Description: Save the current settings to the configuration file
    # Date: 18/03/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def save(self) -> None:
        """
        Save the current settings to the configuration file.
        """
        # Settings section
        self.config_parser[SETTINGS][SETTING_LANGUAGE] = self.language
        self.config_parser[SETTINGS][
            SETTING_SPELLCHECKER_LANGUAGE
        ] = self.spellchecker_language
        self.config_parser[SETTINGS][SETTING_DEFAULT_VIEW] = self.default_view
        self.config_parser[SETTINGS][SETTING_SELECTED_PROFILE] = self.selected_profile
        self.config_parser[SETTINGS][SETTING_USING_DEFAULT_PROFILE] = str(
            self.using_default_profile
        )
        self.config_parser[SETTINGS][SETTING_CUSTOM_PROFILE_PATH] = (
            self.custom_profile_path.as_posix() if self.custom_profile_path else ""
        )
        self.config_parser[SETTINGS][SETTING_OPEN_PROJECT_ON_STARTUP] = str(
            self.open_project_on_startup
        )

        self.config_parser[SETTINGS][SETTING_EDIT_ON_CLONE] = str(self.edit_on_clone)

        with open(self.settings_file_path, "w", encoding="utf-8") as config_file:
            self.config_parser.write(config_file)

        log.info(f"Settings saved to '{self.settings_file_path}'.")
        log.info(f"{self.language = }")
        log.info(f"{self.spellchecker_language = }")
        log.info(f"{self.default_view = }")
        log.info(f"{self.selected_profile = }")
        log.info(f"{self.using_default_profile = }")
        log.info(f"{self.custom_profile_path = }")
        log.info(f"{self.open_project_on_startup = }")
        log.info(f"{self.edit_on_clone = }")

    # ==========================================================================
    # Session data
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: get_last_project_opened
    # Description: Get the last project opened
    # Date: 13/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_last_project_opened(self) -> str:
        """
        Get the last project opened.
        """
        try:
            return self.config_parser[SESSION][SESSION_LAST_PROJECT_OPENED]
        except KeyError:
            log.error(
                f"Session data '{SESSION_LAST_PROJECT_OPENED}' not found in '{self.settings_file_path}'."
            )
            return ""

    # --------------------------------------------------------------------------
    # Method: set_last_project_opened
    # Description: Set the last project opened
    # Date: 13/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_last_project_opened(self, last_project_opened: str) -> None:
        """
        Set the last project opened. If the open project on startup setting is
        disabled, the last project opened is not saved.
        """
        if self.open_project_on_startup is False:
            return

        self.config_parser[SESSION][SESSION_LAST_PROJECT_OPENED] = last_project_opened

        with open(self.settings_file_path, "w") as config_file:
            self.config_parser.write(config_file)

        log.info(
            f"Session data '{SESSION_LAST_PROJECT_OPENED}' saved to '{self.settings_file_path}'."
        )
        log.info(f"{last_project_opened = }")
