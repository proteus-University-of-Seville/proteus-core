# ==========================================================================
# File: test_render_service.py
# Description: pytest file for the PROTEUS render service
# Date: 19/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.configuration.config import Config
from proteus.application.resources.plugins import Plugins
from proteus.services.render_service import RenderService
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH, PROTEUS_SAMPLE_DATA_PATH

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

DEFAULT_TEMPLATE = "default"


@pytest.fixture()
def render_service():
    """
    Fixture for RenderService object

    Loading a custom XSLT avoid using components methods in XSLT (cannot
    be loaded from this test file) but still allows to test XSLT python functions
    from plugins.
    """
    # Mock XSLT config dir
    prev_xslt_dir = Path(Config().profile_settings.xslt_directory)
    Config().profile_settings.xslt_directory = PROTEUS_SAMPLE_DATA_PATH / "xslt"

    # Load plugins
    Plugins().load_plugins(Config().app_settings.plugins_directory)

    # Create service
    service = RenderService()

    # Add plugins XSLT functions
    service.add_functions_to_namespace(Plugins().get_xslt_functions())

    # Do not add components methods since component cannot be instantiated here

    yield service

    # Clean up
    Config().profile_settings.xslt_directory = prev_xslt_dir



@pytest.fixture()
def example_xml() -> ET.Element:
    """
    Fixture for example XML. XML was created from EXAMPLE document
    from example_project.
    """
    xml_path = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project_example_doc.xml"
    return ET.parse(xml_path)


@pytest.fixture()
def example_html() -> str:
    """
    Fixture for example HTML. HTML was created from EXAMPLE document
    from example_project. Generated with default template.
    """
    html_path = (
        PROTEUS_SAMPLE_PROJECTS_PATH / "example_project_example_doc_default_template.html"
    )
    with open(html_path, "r", encoding="utf-8") as f:
        html_string = f.read()
    return html_string


def normalize_string(string: str) -> str:
    """
    Normalize a string to compare it with another string
    """
    string = string.replace("\r\n", "\n").replace("\r", "\n")
    return " ".join(string.strip().split())


# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------

@pytest.mark.order(1)
def test_get_xslt(render_service: RenderService):
    """
    Test for get_xslt method
    """
    # Act -----------------------------
    xslt = render_service._get_xslt(DEFAULT_TEMPLATE)

    # Assert --------------------------
    assert isinstance(
        xslt, ET.XSLT
    ), f"XSLT object must be an instance of ET.XSLT but it is {type(xslt)}"

    assert (
        xslt in render_service._transformations.values()
    ), "XSLT object must be stored in the RenderService object"

@pytest.mark.order(2)
def test_render(
    mocker, render_service: RenderService, example_xml: ET.Element, example_html: str
):
    """
    Test for render method. Plugins has to be loaded and namespace configuration
    has to be re-executed to test the render method.

    NOTE: The output HTML file does not load correctly the images, css and js because
    they are referenced using Proteus custom search paths that require server connection.
    This test only checks the HTML structure and content.
    """
    # Arrange -------------------------

    # Mock StataManager get_current_document method
    mocker.patch(
        "proteus.application.state.manager.StateManager.get_current_document",
        return_value="722GfFiezi5F",
    )

    # Act -----------------------------
    # Test for a valid render
    html_string: str = render_service.render(example_xml, DEFAULT_TEMPLATE)

    # Assert --------------------------
    assert isinstance(
        html_string, str
    ), f"Render result must be an instance of string but it is {type(html_string)}"

    assert (
        html_string == example_html
    ), "Render result does not match with the expected result from the example HTML file"

@pytest.mark.order(3)
def test_render_error(mocker, render_service: RenderService, example_xml: ET.Element):
    """
    Test error handling when the XSLT transformation fails
    """
    # Arrange -------------------------
    
    # Remove known function to force an error
    ns = ET.FunctionNamespace("http://proteus.us.es/utils")
    ns['current_document'] = lambda : None

    # Act -----------------------------
    html_string: str = render_service.render(example_xml, DEFAULT_TEMPLATE)

    # Assert --------------------------

    error_string = "<errors><error>Invalid expression</error><error>runtime error, element 'variable'</error><error>Failed to evaluate the expression of variable 'currentDocumentId'.</error></errors>\n"

    assert isinstance(
        html_string, str
    ), f"Render result must be an instance of string but it is {type(html_string)}"

    assert html_string == error_string, (
        "Render result does not match with the expected result from the example HTML file"
        f"\nRender result: {html_string}"
        f"\nExpected result: {error_string}"
    )


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------
