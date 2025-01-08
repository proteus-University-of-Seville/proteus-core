# ==========================================================================
# File: url_property.py
# Description: PROTEUS url property
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
from urllib.parse import urlparse

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import VALUE_ATTRIBUTE
from proteus.model.properties.property import Property
from proteus.model.properties import URL_PROPERTY_TAG

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: UrlProperty
# Description: Dataclass for PROTEUS url properties
# Date: 22/10/2022
# Version: 0.3
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class UrlProperty(Property):
    """
    Class for PROTEUS url properties.
    """

    # XML element tag name for this class of property (class attribute)
    element_tagname: ClassVar[str] = URL_PROPERTY_TAG
    value: str

    def __post_init__(self) -> None:
        """
        It validates the URL passed as a string.
        """
        # Superclass validation
        super().__post_init__()

        # Default value
        _value: str = str(
            "https://www.us.es/sites/default/files/inline-images/US-marca-principal.png"
        )

        # Value validation
        try:
            _value = str(self.value)
            valid_url = validate_url_string(_value)

            if not valid_url:
                log.warning(
                    f"URL property '{self.name}': Wrong format ({self.value}). Please check."
                )
        except TypeError:
            log.warning(
                f"URL property '{self.name}': Wrong type ({type(self.value)}). Please use str"
            )

        finally:
            # self.value = _value cannot be used when frozen=True
            # https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
            object.__setattr__(self, VALUE_ATTRIBUTE, _value)

    @property
    def is_valid(self) -> bool:
        return validate_url_string(self.value)

    def generate_xml_value(self, _: ET._Element = None) -> str | ET.CDATA:
        """
        It generates the value of the property for its XML element.
        """

        _value = self.value

        return ET.CDATA(_value)


# --------------------------------------------------------------------------
# Function: validate_url_string
# Description: Function to validate a URL string
# Date: 25/09/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
# NOTE: We avoid using external library validators because it was causing
# an issue for some users that were not able to import the library.
# Solution from: https://stackoverflow.com/a/38020041/17947088
def validate_url_string(url_string: str) -> bool:
    """
    Function to validate a URL string.
    """

    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
