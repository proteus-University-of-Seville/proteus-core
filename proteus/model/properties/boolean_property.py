# ==========================================================================
# File: boolean_property.py
# Description: PROTEUS boolean property
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
from proteus.model.properties import BOOLEAN_PROPERTY_TAG

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: BooleanProperty
# Description: Dataclass for PROTEUS boolean properties
# Date: 15/10/2022
# Version: 0.2
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BooleanProperty(Property):
    """
    Class for PROTEUS boolean properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = BOOLEAN_PROPERTY_TAG
    value: bool

    def __post_init__(self) -> None:
        """
        It validates the boolean passed as a string or bool. If it is not valid, it assigns False value.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: bool = False

        # Value validation
        try:
            # If the value is a bool, it is valid
            if isinstance(self.value, bool):
                _value = self.value
            # If the value is a string, it is valid if it is "true" or "false"
            elif isinstance(self.value, str):
                if self.value.lower() not in ["true", "false"]:
                    raise ValueError
                _value = bool(self.value.lower() == "true")
            # If the value is not a bool or a string, it is not valid
            else:
                raise TypeError
        except ValueError:
            log.warning(
                f"Boolean property '{self.name}': Wrong format ({self.value}). Please use 'true' or 'false' -> assigning False value"
            )
        except TypeError:
            log.warning(
                f"Boolean property '{self.name}': Wrong type ({type(self.value)}). Please use bool or str -> assigning False value"
            )
        finally:
            # self.value = _value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """

        # Check string is correct (True or False ignored case)
        assert self.value in [
            True,
            False,
        ], f"booleanProperty '{self.name}' is wrong type. Value must be True or False. Value: {self.value}"

        return str(self.value).lower()
