# ==========================================================================
# File: integer_property.py
# Description: PROTEUS integer property
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
from typing import ClassVar
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
from proteus.model.properties import INTEGER_PROPERTY_TAG

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: IntegerProperty
# Description: Dataclass for PROTEUS integer properties
# Date: 15/10/2022
# Version: 0.2
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegerProperty(Property):
    """
    Class for PROTEUS integer properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = INTEGER_PROPERTY_TAG
    value: int

    def __post_init__(self) -> None:
        """
        It validates the integer passed as a string or int.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: int = int(0)

        # Value validation
        try:
            # If the value is int, it is validated
            if isinstance(self.value, int):
                _value = self.value
            # If the value is str, convert to int
            elif isinstance(self.value, str):
                _value = int(self.value)
            # If the value is not int or str, raise TypeError
            else:
                raise TypeError
        except ValueError:
            log.warning(
                f"Integer property '{self.name}': Wrong format ({self.value}) -> assigning 0 value"
            )
        except TypeError:
            log.warning(
                f"Integer property '{self.name}': Wrong type ({type(self.value)}). Please use int or str -> assigning 0 value"
            )
        finally:
            # self.value = _value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            # TODO if self.value (str) is a float (x.y), will fail. Should we allow floats? (int(float(self.value)))
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """
        return str(self.value)
