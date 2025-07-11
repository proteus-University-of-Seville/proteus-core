# ==========================================================================
# File: property.py
# Description: PROTEUS abstract property
# Date: 27/02/2023
# Version: 0.3
# Author: Amador Durán Toro
#         Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from typing import Any
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import (
    NAME_ATTRIBUTE,
    CATEGORY_ATTRIBUTE,
    INMUTABLE_ATTRIBUTE,
    REQUIRED_ATTRIBUTE,
    TOOLTIP_ATTRIBUTE,
)
from proteus.model.properties import DEFAULT_NAME, DEFAULT_CATEGORY

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: Property (abstract)
# Description: Abstract dataclass for PROTEUS properties
# Date: 17/10/2022
# Version: 0.3
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
# About using __post_init__:
# https://stackoverflow.com/questions/60179799/python-dataclass-whats-a-pythonic-way-to-validate-initialization-arguments
# Dataclasses have a replace(object, value=new_value) function which returns
# a copy of an object with a new value (similar to attr.evolve()).
# https://stackoverflow.com/questions/56402694/how-to-evolve-a-dataclass-in-python
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Property(ABC):
    """
    Abstract class for PROTEUS properties.
    """

    # dataclass instance attributes
    name: str = str(DEFAULT_NAME)
    category: str = str(DEFAULT_CATEGORY)
    value: Any = str()
    tooltip: str = str()
    required: bool = False
    inmutable: bool = False

    def __post_init__(self) -> None:
        """
        It validates name, category, tooltip and inmutable of an abstract PROTEUS property.
        """
        # Name validation
        if not self.name:
            log.warning(
                f"PROTEUS properties must have a '{NAME_ATTRIBUTE}' attribute -> assigning '{DEFAULT_NAME}' as name"
            )
            # self.name = DEFAULT_NAME cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, NAME_ATTRIBUTE, DEFAULT_NAME)

        # Category validation
        if not self.category:
            # self.category = DEFAULT_CATEGORY cannot be used when frozen=True
            object.__setattr__(self, CATEGORY_ATTRIBUTE, DEFAULT_CATEGORY)

        # Required validation
        if not isinstance(self.required, bool):
            # self.required = False cannot be used when frozen=True
            object.__setattr__(self, REQUIRED_ATTRIBUTE, False)

        # Inmutable validation
        if not isinstance(self.inmutable, bool):
            # self.inmutable = False cannot be used when frozen=True
            object.__setattr__(self, INMUTABLE_ATTRIBUTE, False)

        # tooltip validation
        if not self.tooltip:
            # self.tooltip = str() cannot be used when frozen=True
            object.__setattr__(self, TOOLTIP_ATTRIBUTE, str())

    def clone(self, new_value=None) -> "Property":
        """
        It clones the property with a new value if it is not None.
        The new value must be provided as a string.
        :param new_value: new value for the property.
        :return: a copy of the property with the new value.
        """
        if new_value is None:
            return replace(self)

        return replace(self, value=new_value)

    def generate_xml(self) -> ET._Element:
        """
        This template method generates the XML element for the property.
        """
        # element_tagname is a class attribute of each concrete subclass
        property_element: ET._Element = ET.Element(self.element_tagname)
        property_element.set(NAME_ATTRIBUTE, self.name)
        property_element.set(CATEGORY_ATTRIBUTE, self.category)

        if self.tooltip and self.tooltip != str():
            property_element.set(TOOLTIP_ATTRIBUTE, self.tooltip)

        if self.required:
            property_element.set(REQUIRED_ATTRIBUTE, str(self.required).lower())

        if self.inmutable:
            property_element.set(INMUTABLE_ATTRIBUTE, str(self.inmutable).lower())
        # generate_xml_value() is defined in subclasses
        property_element.text = self.generate_xml_value(property_element)

        return property_element

    @abstractmethod
    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        Depending on the type of property, it can be a string or
        a CDATA section.
        """

    def compare(self, other: "Property") -> bool:
        """
        It compares two properties to check if they are equal. If a non-property
        object is provided, it returns False.
        
        :param other: the other property to compare.
        :return: True if both properties are equal comparing their attributes.
        """
        if not isinstance(other, Property):
            return False

        return (
            self.name == other.name
            and self.category == other.category
            and self.tooltip == other.tooltip
            and self.required == other.required
            and self.inmutable == other.inmutable
            and self.value == other.value
        )
