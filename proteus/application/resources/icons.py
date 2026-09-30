# ==========================================================================
# File: dynamic_icons.py
# Description: Manage the icons for PROTEUS application.
# Date: 12/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict
from pathlib import Path
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from strenum import StrEnum
from lxml import etree as ET
from PyQt6.QtGui import QIcon

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta
from proteus.application.configuration.config import Config

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

ICONS_FILE: str = "icons.xml"
DEFAULT_ICON_KEY = ":Proteus-default-icon"


# --------------------------------------------------------------------------
# Class: ProteusIconType
# Description: Enum for PROTEUS icon types
# Date: 15/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ProteusIconType(StrEnum):
    App = "app"
    MainMenu = "main_menu"
    Archetype = "archetype"
    Document = "document"


# --------------------------------------------------------------------------
# Class: Icons
# Description: Manage the icons for PROTEUS application
# Date: 12/02/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class Icons(metaclass=SingletonMeta):
    """
    Handle PROTEUS icons. It can load icons from directories that contain
    an icons configuration file 'icons.xml'. The icons configuration file
    must contain the following structure:

    <icons>
        <type name="type_name" default="default_icon">
            <icon key="icon_key" file="icon_file"/>
            ...
        </type>
        ...
    </icons>

    Where:
    - type_name: Icon type name. It must be a valid ProteusIconType.
    - default_icon: Default icon for the type. It is optional.
    - icon_key: Icon key.
    - icon_file: Icon file path.

    The icons configuration file must be located in the icons directory.

    All the repeated values (included default) defined in the icons file inside
    the profile will override the values defined in the resources
    directory. This allows maintaining default values in the application while
    it is possible to override them.

    This class uses memoization to store the icons already instantiated as
    QIcon objects.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Constructor for Icons class.
    # Date: 26/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self):
        """
        Initializes the Icons class.
        """
        # Icons variable
        self._icons_paths: Dict[ProteusIconType, Dict[str, Path]] = {}

        # Icons memo
        self._icons_memo: Dict[ProteusIconType, Dict[str, QIcon]] = {}
        for icon_type in ProteusIconType:
            self._icons_memo[icon_type] = {}

    # ==========================================================================
    # Helper methods
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: _load_icons
    # Description: Loads the icons from the given directory
    # Date: 12/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _load_icons(self, icons_path: Path) -> None:
        """
        Loads the icons configuration file 'icons.xml' from the given directory.
        Stores the icons paths found in the configuration file.

        :param icons_path: Path to the icons directory.
        """

        # Parse icons file
        icons_file: Path = icons_path / ICONS_FILE

        # Check if icons file exists
        assert icons_file.exists(), (
            f"Icons file '{icons_file}' does not exist. If you are loading icons from the app resources directory, this might crash the application. "
            "If you are loading icons from the profile icons directory, it will just look for png files in the root icons directory."
        )

        resources_icons_tree: ET._ElementTree = ET.parse(icons_file)
        resources_icons_root: ET._Element = resources_icons_tree.getroot()

        # Iterate over icons tag children (type tag) to create each type dictionary
        for type_tag in resources_icons_root.iterchildren():
            # Get name attribute to check if it is a valid icon type
            type_name: str = type_tag.attrib.get("name", None)

            # Check if type name is a valid ProteusIconType
            assert (
                type_name in ProteusIconType._member_map_.values()
            ), f"Icon type '{type_name}' is not a valid ProteusIconType, check {icons_file.as_posix()} file."

            # Initialize type dictionary
            type_dictionary: Dict[str, Path] = {}

            # Get the default icon and store if it exists
            default_icon: str = type_tag.attrib.get("default", None)
            if default_icon is not None:
                type_dictionary[DEFAULT_ICON_KEY] = icons_path / default_icon
            else:
                log.warning(
                    f"Default icon not found for icon type '{type_name}'. This could crash the application. Check {icons_path.as_posix()} file."
                )

            # Iterate over icons tag children icon
            for icon in type_tag.iterchildren():
                # Get key and file attributes for the icon tag
                key = icon.attrib.get("key", None)
                file = icon.attrib.get("file", None)

                if key is None or key == "" or file is None or file == "":
                    log.error(
                        f"Icon key or file are not correctly defined for icon type '{type_name}'. Check {icons_path.as_posix()} file. Key value: {key}, File value: {file}"
                    )
                    continue

                # Check if icon file exists
                file_path: Path = icons_path / file
                if not file_path.exists():
                    log.error(
                        f"Icon file '{file_path}' does not exist. Check {icons_path.as_posix()} file."
                    )
                    continue

                # Add icon to type dictionary
                type_dictionary[key] = file_path

            # Update icons paths dictionary
            if type_name in self._icons_paths:
                self._icons_paths[type_name].update(type_dictionary)
            else:
                self._icons_paths[type_name] = type_dictionary

    # ==========================================================================
    # Public methods
    # ==========================================================================

    def clear(self) -> None:
        """
        Clear all loaded icon paths and memoized QIcon instances. Used when
        the application theme changes: icon layers (baseline theme, active
        theme delta, profile) must be reloaded from scratch so keys resolve
        to the new theme's assets.
        """
        self._icons_paths = {}
        self._icons_memo = {}
        for icon_type in ProteusIconType:
            self._icons_memo[icon_type] = {}

    # --------------------------------------------------------------------------
    # Method: load_icons
    # Description: Load the system icons
    # Date: 12/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def load_icons(self, icons_directory: Path | None) -> bool:
        """
        Loads the icons from the given directory. Returns True if the icons
        were loaded successfully, False otherwise.

        :param icons_directory: Path to the icons directory.

        :return: True if the icons were loaded successfully, False otherwise.
        """

        if icons_directory is None:
            log.error("Icons directory is None.")
            return False

        if icons_directory.exists() and icons_directory.is_dir():
            try:
                self._load_icons(icons_directory)
                return True
            except Exception as e:
                log.error(f"Error loading icons: {e}")
                return False
        else:
            log.error(f"Icons directory '{icons_directory}' does not exist.")
            return False

    # --------------------------------------------------------------------------
    # Method: icon_path
    # Description: Returns the icon path for the given key and type
    # Date: 08/10/2024
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def icon_path(
        self, type: ProteusIconType, key: str = DEFAULT_ICON_KEY
    ) -> Path | None:
        """
        It returns the icon path for the given type and key.

        Archetypes and document icons are looked up in the profile icons directory
        first and then in the app resources icons/archetypes directory if the key
        is not found.

        :param type: Icon type.
        :param key: Icon key.
        :return: Icon path or None if the icon is not found.
        """
        if type not in self._icons_paths:
            log.critical(f"Type {type} not found in dynamic icons dictionary.")
            return None

        icons_paths = self._icons_paths[type]

        # Special case for archetypes and document acronyms. In order to reduce the number
        # of steps needed to add archetypes, we will search for the icon based on the key
        # name in the icons directories.
        if key not in icons_paths and type in [
            ProteusIconType.Archetype,
            ProteusIconType.Document,
        ]:
            log.debug(
                f"Icon key '{key}' not found for type '{type}', trying to find '{key}.png' in profile icons directories."
            )

            # Check if key exists in any of the directories
            alternative_icons_profile_path = (
                Config().profile_settings.icons_directory / f"{key}.png"
            )
            if alternative_icons_profile_path.exists():
                return alternative_icons_profile_path

            log.debug(
                f"Icon '{key}.png' not found in '{alternative_icons_profile_path}'. Using default icon."
            )

            key = DEFAULT_ICON_KEY

        # Base case, key not found and not archetype type
        if key not in icons_paths and type != ProteusIconType.Archetype:
            log.debug(
                f"Icon key '{key}' not found for type '{type}', using default icon"
            )
            key = DEFAULT_ICON_KEY

        # Default icon may not exist, log a critical message
        icon_path = self._icons_paths[type].get(key, None)
        if icon_path is None:
            log.critical(
                f"Icon path not found for type '{type}' and key '{key}', check default icons."
            )

        return icon_path

    # --------------------------------------------------------------------------
    # Method: icon
    # Description: Returns the icon for the given key and type
    # Date: 12/02/2024
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def icon(self, type: ProteusIconType, key: str = DEFAULT_ICON_KEY) -> QIcon:
        """
        It returns the icon (QIcon) for the given type and key. Icons are
        stored in a memo to avoid creating multiple QIcon objects for the same
        icon.

        :param type: Icon type.
        :param key: Icon key.
        :return: Icon (QIcon) for the given type and key. If the icon is not
        found, it returns an empty QIcon.
        """
        # Check if icon is already in memo
        if key in self._icons_memo[type]:
            return self._icons_memo[type][key]

        icon_path = self.icon_path(type, key)
        icon = QIcon(icon_path.as_posix()) if icon_path else QIcon()
        self._icons_memo[type][key] = icon
        return icon
