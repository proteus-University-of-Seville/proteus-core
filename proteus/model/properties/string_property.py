# ==========================================================================
# File: string_property.py
# Description: PROTEUS string property
# Date: 27/02/2023
# Version: 0.3
# Author: Amador Durán Toro
#         Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
import re
from dataclasses import dataclass
from typing import ClassVar

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import VALUE_ATTRIBUTE
from proteus.model.properties.property import Property
from proteus.model.properties import STRING_PROPERTY_TAG

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: StringProperty
# Description: Dataclass for PROTEUS string properties
# Date: 15/10/2022
# Version: 0.2
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StringProperty(Property):
    """
    Class for PROTEUS string properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = STRING_PROPERTY_TAG
    value: str

    def __post_init__(self) -> None:
        """
        Turns value into a string, there is nothing to validate.
        """
        # Superclass validation
        super().__post_init__()

        # self.value = str(self.value) cannot be used when frozen=True
        # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
        object.__setattr__(self, VALUE_ATTRIBUTE, str(self.value))

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """
        # XML 1.0 valid characters: https://www.w3.org/TR/xml/#charsets
        # Remove any character that does not match this pattern
        pattern = re.compile(
            "["
            "\U00000009\U0000000A\U0000000D"
            "\U00000020-\U0000D7FF"
            "\U0000E000-\U0000FFFD"
            "\U00010000-\U0010FFFF"
            "]+",
            re.UNICODE,
        )
        sanitized_value = "".join(pattern.findall(self.value))

        return ET.CDATA(sanitized_value)
