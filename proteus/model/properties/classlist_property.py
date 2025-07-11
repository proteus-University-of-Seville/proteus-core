# ==========================================================================
# File: classlist_property.py
# Description: PROTEUS class list property
# Date: 27/02/2023
# Version: 0.3
# Author: Amador Durán Toro
#         Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from dataclasses import dataclass
from typing import ClassVar, List
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusClassTag, VALUE_ATTRIBUTE
from proteus.model.properties.property import Property
from proteus.model.properties import CLASSLIST_PROPERTY_TAG, CLASS_TAG


# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: ClassListProperty
# Description: Class for PROTEUS ClassList properties
# Date: 22/10/2022
# Version: 0.2
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
#         José María Delgado Sánchez
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassListProperty(Property):
    """
    Class for PROTEUS class-tag-list properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = CLASSLIST_PROPERTY_TAG
    value: List[ProteusClassTag]

    def __post_init__(self) -> None:
        """
        It validates the value of the property is a list or a space-separated string.
        Repeated values are removed.
        """
        # Superclass validation
        super().__post_init__()

        # TODO: how can we check whether class names are valid at this moment?


        # Check if the value is a string
        if isinstance(self.value, str):
            object.__setattr__(self, VALUE_ATTRIBUTE, self.value.split())

        # Check if the value is a list
        if not isinstance(self.value, list):
            log.warning(
                f"ClassListProperty: {self.name} value is not a list but '{type(self.value)}', setting it to an empty list"
            )
            object.__setattr__(self, VALUE_ATTRIBUTE, list())

        # Check values are not repeated
        value_set = set(self.value)
        if len(value_set) != len(self.value):
            log.warning(
                f"ClassListProperty: {self.name} contains repeated values, setting it to a list with unique values. \
                This may affect the original order of the list. Original value: {self.value}, new value: {value_set}"
            )
            object.__setattr__(self, VALUE_ATTRIBUTE, list(value_set))

        # Check for None values
        if None in self.value:
            log.warning(
                f"ClassListProperty: {self.name} contains None values, setting it to a list without None values"
            )
            object.__setattr__(self, VALUE_ATTRIBUTE, [value for value in self.value if value is not None])

    def generate_xml_value(self, property_element: ET._Element) -> str | ET.CDATA | None:
        """
        It generates the value of the property for its XML element.
        In this case, it adds one <class> child for each class tag.
        """
        for class_name in self.value:
            class_element = ET.SubElement(property_element, CLASS_TAG)
            class_element.text = class_name

        # Returning None avoid the XML to be printed in a single line
        # https://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output
        return None