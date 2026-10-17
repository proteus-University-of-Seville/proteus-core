# ==========================================================================
# File: template.py
# Description: PROTEUS xslt template model
# Date: 14/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from lxml import etree as ET
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path


# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------


# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

TEMPLATE_CONFIG_FILE: str = "template.xml"

# XSLT templates config file tags and attributes
XSLT_TEMPLATE_TAG            = "template"
XSLT_ENTRY_POINTS_TAG        = "entryPoints"
XSLT_ENTRY_POINT_TAG         = "entryPoint"
XSLT_DEPENCENCIES_TAG        = "dependencies"
XSLT_PLUGIN_DEPENDENCY_TAG   = "pluginDependency"

XSLT_NAME_ATTRIBUTE      = "name"
XSLT_LANGUAGE_ATTRIBUTE  = "language"
XSLT_FILE_ATTRIBUTE      = "file"
XSLT_DEFAULT_ATTRIBUTE   = "default"
XSLT_OUTPUT_ATTRIBUTE    = "output"

# Output formats. HTML templates are views shown in the application; any other
# format (e.g. LaTeX) is only used by export strategies.
TEMPLATE_OUTPUT_HTML: str  = "html"
TEMPLATE_OUTPUT_LATEX: str = "latex"



# --------------------------------------------------------------------------
# Class: Tempalte
# Description: Class for PROTEUS xslt templates
# Date: 14/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
@dataclass
class Template:

    name: str
    path: Path
    default_entrypoint: Path = None
    entrypoints: Dict[str, Path] = None
    plugin_dependencies: List[str] = None
    output_format: str = TEMPLATE_OUTPUT_HTML

    @property
    def is_view(self) -> bool:
        """
        True if the template generates HTML and can be shown as a view.
        """
        return self.output_format == TEMPLATE_OUTPUT_HTML

    # ----------------------------------------------------------------------
    # Method     : load
    # Description: Load the template from the given path
    # Date       : 14/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def load(template_path: Path) -> "Template":

        template_name: str

        # Look for the template.xml file inside the folder
        template_file: Path = template_path / TEMPLATE_CONFIG_FILE
        assert (
            template_file.exists()
        ), f"XSLT template configuration file {template_file} does not exist in {template_path}! Check your XSLT directory."

        # Parse template file
        template_tree: ET._ElementTree = ET.parse(template_file)
        template_root: ET._Element = template_tree.getroot()

        # Get the template name
        template_name: str = template_root.get(XSLT_NAME_ATTRIBUTE)

        # Check name attribute is not empty
        assert (
            template_name is not None and template_name != ""
        ), f"Name attribute not found in template tag for template {template_file}"

        # Get the output format (optional, HTML by default)
        output_format: str = template_root.get(
            XSLT_OUTPUT_ATTRIBUTE, TEMPLATE_OUTPUT_HTML
        ).strip().lower()

        # Return the template object
        template = Template(
            name=template_name,
            path=template_path,
            output_format=output_format,
        )

        template._load_entrypoints()
        template._load_dependencies()

        log.info(f"Template '{template_name}' loaded from {template_path}")

        return template

    # ----------------------------------------------------------------------
    # Method     : _load_entrypoints
    # Description: Loads template entry points from the template configuration file.
    # Date       : 14/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _load_entrypoints(self) -> None:
        """
        Loads template entry points from the template configuration file.
        """

        self.default_entrypoint: Path = None
        self.entrypoints: Dict[str, Path] = {}

        root: ET._Element = ET.parse(self.path / TEMPLATE_CONFIG_FILE).getroot()

        self.entrypoints: Dict[str, Path] = {}

        # Set default entry point in case there is no entryPoints tag
        entrypoints_element: ET._Element = root.find(XSLT_ENTRY_POINTS_TAG)

        # Check entryPoints tag exists
        assert (
            entrypoints_element is not None
        ), f"'entryPoints' tag not found in template {self.path}"

        default_entrypoint_file: str = entrypoints_element.get(XSLT_DEFAULT_ATTRIBUTE)
        self.default_entrypoint: Path = self.path / default_entrypoint_file
        assert (
            self.default_entrypoint.exists()
        ), f"Default entry point file {default_entrypoint_file} does not exist in {self.path}!"

        # Iterate over entryPoints tag children to get the entryPoint for the current language or the default one
        for entrypoint in entrypoints_element.findall(XSLT_ENTRY_POINT_TAG):
            # Get language and file attributes for the entryPoint tag
            lang = entrypoint.get(XSLT_LANGUAGE_ATTRIBUTE)
            file = entrypoint.get(XSLT_FILE_ATTRIBUTE)

            # Check xml is well formed
            assert (
                lang is not None and file is not None
            ), f"Language or file attribute not found in entryPoint tag for template {self.path}"

            # Form the entry point file path
            entrypoint_file_path: Path = self.path / file

            # Check if the template entry point file exists
            assert (
                entrypoint_file_path.exists()
            ), f"XSLT template entry point file {entrypoint_file_path} does not exist in {self.path}!"

            # Add the entry point to the dictionary
            self.entrypoints[lang] = entrypoint_file_path


    # ----------------------------------------------------------------------
    # Method     : _load_dependencies
    # Description: Loads template dependencies from the template configuration file.
    # Date       : 14/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _load_dependencies(self) -> None:
        """
        Loads template dependencies from the template configuration file.
        """

        self.plugin_dependencies: List[str] = []

        root: ET._Element = ET.parse(self.path / TEMPLATE_CONFIG_FILE).getroot()

        self.plugin_dependencies: List[str] = []

        # Get the dependencies tag
        dependencies: ET._Element = root.find(XSLT_DEPENCENCIES_TAG)

        # Check dependencies tag exists
        assert (
            dependencies is not None
        ), f"'dependencies' tag not found in template {self.path}"

        # Iterate over dependencies tag children to get the pluginDependency
        for dependency in dependencies.findall(XSLT_PLUGIN_DEPENDENCY_TAG):
            # Get name attribute for the pluginDependency tag
            dependency_name = dependency.get(XSLT_NAME_ATTRIBUTE)

            # Check xml is well formed
            assert (
                dependency_name is not None and dependency_name != ""
            ), f"Name attribute not found in pluginDependency tag for template {self.path}"

            # Add the template dependency to the list
            self.plugin_dependencies.append(dependency_name)

