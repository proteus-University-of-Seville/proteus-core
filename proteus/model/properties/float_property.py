# ==========================================================================
# File: float_property.py
# Description: PROTEUS float property
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
from proteus.model.properties import FLOAT_PROPERTY_TAG

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: FloatProperty
# Description: Dataclass for PROTEUS float properties
# Date: 15/10/2022
# Version: 0.2
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FloatProperty(Property):
    """
    Class for PROTEUS real properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = FLOAT_PROPERTY_TAG
    value: float

    def __post_init__(self) -> None:
        """
        It validates the float passed as a string, float or int.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: float = float(0.0)

        # Value validation
        try:
            # If the value is a float, it is valid
            if isinstance(self.value, float):
                _value = self.value
            # If the value is a string or int, convert it to float
            elif isinstance(self.value, (str, int)):
                _value = float(self.value)
            # If the value is not a float or a string, use default value
            else:
                raise TypeError
        except ValueError:
            # self.value = _value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            log.warning(
                f"Float property '{self.name}': Wrong format ({self.value}) -> assigning 0.0 value"
            )
        except TypeError:
            log.warning(
                f"Float property '{self.name}': Wrong type ({type(self.value)}). Please use float or str -> assigning 0.0 value"
            )
        finally:
            # self.value = float(self.value) cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """
        return str(self.value)
