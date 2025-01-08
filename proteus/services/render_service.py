# ==========================================================================
# File: render_service.py
# Description: Render service for document rendering
# Date: 29/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import List, Dict
from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports (starting from root)
# --------------------------------------------------------------------------

from proteus.model.template import Template
from proteus.application.resources.plugins import Plugins
from proteus.application.configuration.config import Config

# logging configuration
log = logging.getLogger(__name__)

FUNCTION_NAMESPACE = "http://proteus.us.es/utils"
NAMESPACE_PREFIX = "proteus-utils"


# --------------------------------------------------------------------------
# Class: RenderService
# Description: Class for render service
# Date: 29/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class RenderService:
    """
    Handle the logic for rendering documents. Store the XSLT transformation
    objects.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Initialize the RenderService object. Load the XSLT
    #              templates.
    # Date       : 29/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initialize the RenderService object. Load the XSLT templates.
        """
        # Store the XSLT transformation objects
        self._transformations: Dict[str, ET.XSLT] = {}

        # Templates
        self._templates: Dict[str, Template] = {}

        # Namespace configuration for the XSLT functions
        self._namespace_configuration()

        # Load the XSLT templates
        self._load_templates()

        log.info("RenderService initialized")

    # ----------------------------------------------------------------------
    # Method     : _namespace_configuration
    # Description: Configuration setup for the XSLT functions. This allows
    #              to use custom python functions in the XSLT templates.
    # Date       : 29/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _namespace_configuration(self) -> None:
        """
        Configuration setup for the XSLT functions. This allows to use
        custom python functions in the XSLT templates using a known prefix.
        """
        # Namespace for the XSLT functions
        ns = ET.FunctionNamespace(FUNCTION_NAMESPACE)
        ns.prefix = NAMESPACE_PREFIX

    # ----------------------------------------------------------------------
    # Method     : _load_templates
    # Description: Load the XSLT templates from the templates directory.
    # Date       : 14/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _load_templates(self) -> None:
        """
        Load the XSLT templates from the templates directory defined in the
        config class.
        """
        loaded_plugins: List[str] = Plugins().get_plugins()

        # Iterate over XSLT directory folders
        for xslt_folder in Config().profile_settings.xslt_directory.iterdir():
            # Check if folder is a directory
            if xslt_folder.is_file():
                log.warning(
                    f"Unexpected item in XSLT directory: {xslt_folder}. It will be ignored."
                )
                continue
            else:
                try:
                    # Load the template
                    template = Template.load(xslt_folder)

                    # Check for plugin dependencies
                    for plugin in template.plugin_dependencies:
                        assert (
                            plugin in loaded_plugins
                        ), f"XSLT template {template.name} depends on plugin {plugin}, which is not loaded!"

                    # Store the template
                    self._templates[template.name] = template

                except Exception as e:
                    log.critical(
                        f"Error loading XSLT template {xslt_folder}. The template will be ignored. Error: {e}"
                    )

        assert self._templates, "No valid XSLT templates found in the XSLT directory!"

    # ----------------------------------------------------------------------
    # Method     : get_xslt
    # Description: Get the XSLT transformation object for the given template_name.
    #              If the object is not found, create it from the xslt file.
    # Date       : 29/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _get_xslt(self, template_name) -> ET.XSLT:
        """
        Get the XSLT transformation object for the given template_name. If the
        object is not found, create it from the xslt file.
        """
        transform: ET.XSLT = None

        if template_name in self._transformations:
            transform = self._transformations[template_name]
        else:
            assert (
                template_name in self._templates
            ), f"Template {template_name} not found in the XSLT directory!"

            # Use the default entrypoint if the language is not found
            template = self._templates[template_name]
            entrypoint: Path
            if Config().app_settings.language in template.entrypoints:
                entrypoint = template.entrypoints[Config().app_settings.language]
            else:
                entrypoint = template.default_entrypoint

            # Create the transformer from the xsl file
            try:
                transform = ET.XSLT(ET.parse(entrypoint.as_posix()))
            except Exception as e:
                log.critical(
                    f"Error creating XSLT transformation object for template '{template_name}'. Error: {e}"
                )
                error_element_str = f'<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"> \
                                      <xsl:output method="html" doctype-public="XSLT-compat" omit-xml-declaration="yes" encoding="UTF-8" indent="yes" /> \
                                      <xsl:template match="/"> \
                                      <hmtl> \
                                          <body> \
                                          <p>{e}</p> \
                                          </body> \
                                      </hmtl> \
                                      </xsl:template> \
                                      </xsl:transform>'
                return ET.XSLT(ET.XML(error_element_str))

            # Store the transformation object for future use
            if Config().app_settings.xslt_debug_mode is False:
                self._transformations[template_name] = transform

        return transform

    # ----------------------------------------------------------------------
    # Method     : render
    # Description: Render the given xml using the xslt template.
    # Date       : 29/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def render(self, xml: ET.Element, template_name: str) -> str:
        """
        Render the given xml using the template_name template.
        """
        transform = self._get_xslt(template_name)
        try:
            result_tree = transform(xml)
        except Exception:
            # Print the errors found while rendering and create an error tree to return
            result_tree = ET.Element("errors")
            for error in transform.error_log:
                error_string = f"Line {error.line}, column {error.column}: {error.message} \n Domain: {error.domain} \n Type: {error.type} \n Level: {error.level} \n Filename: {error.filename} \n"
                log.critical(
                    f"Error found while rendering xml using template {template_name}: \n {error_string}"
                )

                error_element = ET.SubElement(result_tree, "error")
                error_element.text = error.message

        html_string = ET.tostring(
            result_tree, encoding="unicode", pretty_print=True, method="html"
        )
        return html_string

    # ----------------------------------------------------------------------
    # Method     : get_templates
    # Description: Get the available xslt templates in the xslt folder.
    # Date       : 29/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_templates(self) -> List[Template]:
        """
        Get the available xslt templates in the xslt folder.
        """
        return list(self._templates.values())

    # ----------------------------------------------------------------------
    # Method     : add_functions_to_namespace
    # Description: Add functions to the XSLT namespace
    # Date       : 10/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_functions_to_namespace(self, functions: Dict[str, callable]) -> None:
        """
        Add functions to the XSLT namespace.

        Functions may be called using the namespace prefix defined in the
        FUNCTION_NAMESPACE constant and the function name.

        Example: <xsl:value-of select="proteus-utils:function_name()"/>
        """
        ns = ET.FunctionNamespace(FUNCTION_NAMESPACE)

        for name, func in functions.items():
            ns[name] = func
