# ==========================================================================
# File: date_property.py
# Description: PROTEUS date property
# Date: 27/02/2023
# Version: 0.3
# Author: Amador Durán Toro
#         Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from datetime import datetime, date
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
from proteus.model.properties import DATE_PROPERTY_TAG, DATE_FORMAT

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: DateProperty
# Description: Dataclass for PROTEUS date properties (YYYY-MM-DD)
# Date: 15/10/2022
# Version: 0.2
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DateProperty(Property):
    """
    Class for PROTEUS date properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = DATE_PROPERTY_TAG
    value: date

    def __post_init__(self) -> None:
        """
        It validates the date passed as a string.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: date = date.today()

        # Value validation
        try:
            # If the value is a date, it is assigned directly
            if isinstance(self.value, date):
                _value = self.value
            # If the value is a string, it is parsed to date
            elif isinstance(self.value, str):
                _value = datetime.strptime(self.value, DATE_FORMAT).date()
            # If the value is not a date or a string, it is not valid
            else:
                raise TypeError
        except ValueError:
            log.warning(
                f"Date property '{self.name}': Wrong format ({self.value}). Please use YYYY-MM-DD -> assigning today's date"
            )
        except TypeError:
            log.warning(
                f"Date property '{self.name}': Wrong type ({type(self.value)}). Please use str or datetime.date -> assigning today's date"
            )
        finally:
            # self.value = value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """

        _value = self.value

        # Check value is instance of time class before converting it to string
        assert isinstance(
            _value, date
        ), f"dateProperty '{self.name}' is not 'date' class. Value type: {type(_value)}"

        return _value.strftime(DATE_FORMAT)
