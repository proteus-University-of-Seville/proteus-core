# ==========================================================================
# File: code_property.py
# Description: PROTEUS code property
# Date: 10/11/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from dataclasses import dataclass
from typing import ClassVar, Any
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import VALUE_ATTRIBUTE
from proteus.model.properties.property import Property
from proteus.model.properties import (
    CODE_PROPERTY_TAG,
    PREFIX_TAG,
    NUMBER_TAG,
    SUFFIX_TAG,
)

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: ProteusCode
# Description: Class for PROTEUS code objects.
# Date: 10/11/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
@dataclass
class ProteusCode:
    """
    Class for PROTEUS code objects. It is used to represent a code in a
    sequence. The codes are composed by prefix, identifier and optional
    suffix. Identifier is an integer that is padded with 3 zeros to the left.

    ProteusCode objects can calculate the next code in the sequence. The
    identifier is incremented by one and the prefix and suffix are kept.

    TODO: Allow custom padding length.
    TODO: Allow non-integer sequences (e.g. A,B,C,...)
    TODO: Allow sub-sequences (e.g. 1,2,3,...,1.1,1.2,1.3,...)
    """

    # Instance attributes
    prefix: str = str()
    number: str = str()
    suffix: str = str()

    def __post_init__(self) -> None:
        """
        Validates the ProteusCode object. Checks that the prefix is a string,
        the number is an integer and the suffix is a string. The prefix
        cannot be empty string and the number cannot be negative or zero.
        """
        # Force prefix and suffix to be strings if None
        if self.prefix is None:
            self.prefix = str()
        if self.suffix is None:
            self.suffix = str()

        assert isinstance(
            self.prefix, str
        ), f"ProteusCode prefix must be string but it is {type(self.prefix)}"
        assert isinstance(
            self.number, (str, int)
        ), f"ProteusCode number must be str or int but it is {type(self.number)}"
        assert isinstance(
            self.suffix, str
        ), f"ProteusCode suffix must be string but it is {type(self.suffix)}"

        # Normalize number to have 3 digits if less than 3
        try:
            number = int(self.number)

            assert number > 0, "ProteusCode number must be greater than zero"

            self.number = f"{number:03d}"
        except ValueError:
            log.warning(
                f"ProteusCode number must be composed by digits but it is '{self.number}' -> assigning default value 1"
            )
            self.number = "1".zfill(3)


    def to_string(self) -> str:
        """
        Returns the string representation of the PROTEUS code. The number is converted to string
        and padded with zeros to the left to have a length of 3 characters.
        """
        return f"{self.prefix}{self.number}{self.suffix}"

    def next(self) -> "ProteusCode":
        """
        Returns the next code in the sequence. The number is incremented by one and the prefix
        and suffix are kept.
        """
        next_number = int(self.number) + 1
        return ProteusCode(self.prefix, f"{next_number:03d}", self.suffix)

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if the codes are equal, False otherwise.

        :param Any other: Object to compare
        :return bool: True if the codes are equal, False otherwise
        """
        if not isinstance(other, ProteusCode):
            return False

        return (
            self.prefix == other.prefix
            and self.number == other.number
            and self.suffix == other.suffix
        )
    
    # TODO: Implement __hash__ method?


# --------------------------------------------------------------------------
# Class: CodeProperty
# Description: Dataclass for PROTEUS integer properties
# Date: 10/11/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CodeProperty(Property):
    """
    Class for PROTEUS code properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = CODE_PROPERTY_TAG
    value: ProteusCode

    def __post_init__(self) -> None:
        """
        It validates the integer passed as a ProteusCode.

        NOTE: str not supported because there is no parsing convention yet.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: ProteusCode = ProteusCode(prefix="DEFAULT", number="1", suffix="")

        # Value validation
        try:
            if isinstance(self.value, ProteusCode):
                _value = self.value
            else:
                raise TypeError
        except TypeError:
            log.warning(
                f"Code property '{self.name}': Wrong type ({type(self.value)}). Please use ProteusCode object -> assigning default value prefix='DEFAULT', identifier=1, suffix=''"
            )
        finally:
            # self.value = value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    def generate_xml_value(
        self, property_element: ET._Element = None
    ) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """
        prefix_element = ET.SubElement(property_element, PREFIX_TAG)
        prefix_element.text = ET.CDATA(self.value.prefix)

        number_element = ET.SubElement(property_element, NUMBER_TAG)
        number_element.text = str(self.value.number)

        suffix_element = ET.SubElement(property_element, SUFFIX_TAG)
        suffix_element.text = ET.CDATA(self.value.suffix)

        # Returning None avoid the XML to be printed in a single line
        # https://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output
        return None
