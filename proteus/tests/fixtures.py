# ==========================================================================
# File: property_fixtures.py
# Description: pytest fixtures for testing PROTEUS properties
# Date: 22/10/2022
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================
# About pytest fixtures: 
# https://docs.pytest.org/en/7.1.x/explanation/fixtures.html#about-fixtures
#
# Pytest fixtures are called automatically from function tests. For the 
# moment, the "fixtures" in this module are not actually pytest fixtures but 
# repeated code extracted as functions.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET
import yaml

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.tests import PROTEUS_PROJECT_DATA_FILE
from proteus.model import NAME_ATTRIBUTE, CATEGORY_ATTRIBUTE, CHOICES_ATTRIBUTE, ProteusID
from proteus.model.properties import \
    Property,                      \
    DEFAULT_NAME,                  \
    DEFAULT_CATEGORY,              \
    CLASS_TAG,                     \
    PropertyFactory,               \
    STRING_PROPERTY_TAG

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def create_property_element(
    property_tag: str = STRING_PROPERTY_TAG,
    name: str = DEFAULT_NAME,
    category: str = DEFAULT_CATEGORY,
    tooltip: str = str(),
    required: bool | str = False,
    inmutable: bool | str = False,
) -> ET._Element:
    """
    Create a property XML element with the given parameters. Tooltip,
    required and inmutable attributes will be set if its value is True
    (non-empty string for tooltip).

    :param name: Name of the property. Default is an empty string.
    :param category: Category of the property. Default is an empty string.
    :param tooltip: Tooltip of the property. Default is an empty string.
    :param required: Required attribute of the property. Default is False.
    :param inmutable: Inmutable attribute of the property. Default is False.
    :param property_tag: Tag of the property element. Default is "string".
    :return: The created XML element.
    """
    property_element: ET._Element = ET.Element(property_tag)

    property_element.set(NAME_ATTRIBUTE, name)
    property_element.set(CATEGORY_ATTRIBUTE, category)
    if tooltip.strip() != "":
        property_element.set("tooltip", tooltip)

    if required:
        property_element.set("required", str(required).lower())

    if inmutable:
        property_element.set("inmutable", str(inmutable).lower())

    return property_element

def create_property(property_tag, name, category, value, choices = None) -> tuple[Property,str,str]:
    """
    It creates a PROTEUS property using the tag, name, category and value
    passed as arguments. It returns a tuple containing the new property, 
    the name, and the category values, which are set to default in case
    they were not set.
    """
    # Create XML element for property
    property_element = ET.Element(property_tag)

    # Process name
    if name:
        property_element.set(NAME_ATTRIBUTE, name)
    else:
        name = DEFAULT_NAME

    # Process category
    if category:
        property_element.set(CATEGORY_ATTRIBUTE, category)
    else:
        category = DEFAULT_CATEGORY

    # Set value as a string
    property_element.text = str(value)

    # Set choices attribute if needed (EnumProperty only)
    if choices is not None:
        property_element.set(CHOICES_ATTRIBUTE, choices)

    # Add <class> children if needed (ClasslistProperty only)
    for class_name in str(value).split():
        class_element = ET.SubElement(property_element, CLASS_TAG)
        class_element.text = class_name
  
    # Create property from XML element
    property = PropertyFactory.create(property_element)

    # return tuple(property,name,category)
    return (property, name, category)

def get_root(path) -> ET.Element:
    """
    Helper function that returns the root element of an xml file.
    :param path: Path to the xml file.
    :return: Root element of the xml file.
    """
    # Parser to avoid conflicts with CDATA
    parser = ET.XMLParser(strip_cdata=False)
    element = ET.parse(path, parser = parser)
    return element.getroot()

class SampleData:
    """
    SampleData class provides an interface to access the sample data used in
    the tests. Objects are accessed using an intuitive name instead of the
    ProteusID. This is done by mapping the ProteusIDs with a new verbose name
    when creating the sample data.

    By default, all the objects and documents are located in the same project
    example_project. 
    """

    sample_data: Dict[str, Dict[str, str]] = None

    @classmethod
    def load(cls) -> None:
        """
        Load the yaml file containing the sample data.
        """
        with open(PROTEUS_PROJECT_DATA_FILE, "r") as f:
            cls.sample_data = yaml.safe_load(f)

    @classmethod
    def get(cls, name: str, project_name="example_project") -> ProteusID:
        """
        Get the ProteusID of the object or document with the given name.

        If no project name is given, the default project is 'example_project'.

        :param name: Name of the object or document.
        :param project_name: Name of the project.
        :return: ProteusID of the object or document.
        """
        if cls.sample_data is None:
            cls.load()

        try:
            return ProteusID(cls.sample_data[project_name][name])
        except KeyError:
            raise KeyError(f"Object or document with name '{name}' not found in project '{project_name}' in sample data file.")
        