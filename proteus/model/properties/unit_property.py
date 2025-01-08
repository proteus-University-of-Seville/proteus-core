# ==========================================================================
# File: unit_property.py
# Description: PROTEUS unit property
# Date: 17/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from dataclasses import dataclass
from typing import ClassVar, List, Any
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import VALUE_ATTRIBUTE, UNITS_ATTRIBUTE
from proteus.model.properties.property import Property
from proteus.model.properties import UNIT_PROPERTY_TAG, VALUE_TAG, UNIT_TAG


# logging configuration
log = logging.getLogger(__name__)


@dataclass
class Measurement:
    """
    Class for PROTEUS measurements (value and unit tuple).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """
        It validates the value is a float or a string that can be
        converted into float and the unit is not empty.
        """
        # Validate the value is not None and can be converted to a number
        assert self.value is not None, "Measurement class value is None"

        if isinstance(self.value, (int, float)):
            self.value = float(self.value)
        elif isinstance(self.value, str):
            try:
                self.value = float(self.value)
            except ValueError:
                raise ValueError(
                    f"Measurement class value is not a number: '{self.value}'"
                )
        else:
            raise ValueError(
                f"Measurement class value is not a float or a string: '{self.value}' of type '{type(self.value)}'"
            )

        # Validate the unit is not empty
        assert isinstance(self.unit, str), "Measurement class unit is not a string"
        assert self.unit.strip() != "", "Measurement class unit is empty"
        assert self.unit.strip().split() == [
            self.unit
        ], "Measurement class unit contains more than one word (spaces)"

    def __eq__(self, other: Any) -> bool:
        """
        Return True if the value and unit of the other Measurement object are

        :param Any other: Object to compare
        :return bool: True if the value and unit of the other Measurement object are equal
        """
        if not isinstance(other, Measurement):
            return False

        return self.value == other.value and self.unit == other.unit

    def to_string(self) -> str:
        """
        Returns the string representation of the PROTEUS measurement. The value
        is converted to a string and stripped of trailing zeros. The unit is
        appended to the value separated by a space.
        """
        return f"{self.value:g} {self.unit}"


# --------------------------------------------------------------------------
# Class: UnitProperty
# Description: Class for PROTEUS unit properties
# Date: 17/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class UnitProperty(Property):
    """
    Class for PROTEUS unit properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = UNIT_PROPERTY_TAG
    value: Measurement = None
    units: List[str] = None

    # --------------------------------------------------------------------------
    # Method: __post_init__
    # Date: 17/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __post_init__(self) -> None:
        """
        It validates the value is a Measurement object and the units list is not empty.
        """
        # Superclass validation
        super().__post_init__()

        # Units validation
        if isinstance(self.units, str):
            object.__setattr__(self, UNITS_ATTRIBUTE, self.units.split())
        elif not isinstance(self.units, list):
            raise ValueError(
                f"UnitProperty class units is not a list: '{self.units}' of type '{type(self.units)}'"
            )

        assert len(self.units) > 0, "UnitProperty class units list is empty"

        # Validate value is a Measurement object
        _value = Measurement(value=0, unit=self.units[0])

        if not isinstance(self.value, Measurement):
            log.warning(
                f"Unit property '{self.name}': Wrong type ({type(self.value)}). Please use Measurement object -> assigning default value 0 {self.units[0]}"
            )
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

        # Validate value unit is in the units list
        if self.value.unit not in self.units:
            log.warning(
                f"Unit property '{self.name}': Value unit '{self.value.unit}' not in units list -> assigning first unit '{self.units[0]}'"
            )
            self.value.unit = self.units[0]

    # --------------------------------------------------------------------------
    # Method: generate_xml
    # Date: 17/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def generate_xml(self) -> ET._Element:
        """
        This template method generates the XML element for the UnitProperty.
        Adds the units attribute to the XML element.

        :return: XML element for the UnitProperty.
        """
        property_element = super().generate_xml()

        # Units generation
        property_element.set(UNITS_ATTRIBUTE, " ".join(self.units))

        return property_element

    # --------------------------------------------------------------------------
    # Method: generate_xml_value
    # Date: 17/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def generate_xml_value(
        self, property_element: ET._Element = None
    ) -> str | ET.CDATA | None:
        """
        It generates the value of the property for its XML element. The value and
        unit are stored in different tags.

        :param property_element: XML element for the property.
        :return: None to avoid the XML to be printed in a single line.
        """
        value_element = ET.SubElement(property_element, VALUE_TAG)
        value_element.text = str(self.value.value)

        unit_element = ET.SubElement(property_element, UNIT_TAG)
        unit_element.text = str(self.value.unit)

        # Returning None avoid the XML to be printed in a single line
        # https://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output
        return None

    # --------------------------------------------------------------------------
    # Method: compare
    # Date: 17/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def compare(self, other: "UnitProperty") -> bool:
        """
        It compares the values of two UnitProperty objects.

        :param other: UnitProperty object to compare.
        :return: True if the attributes values are equal, False otherwise.
        """
        base_attributes = super().compare(other)
        return (
            base_attributes and self.units == other.units and self.value == other.value
        )
