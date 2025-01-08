# ==========================================================================
# File: float_property_input.py
# Description: Float property input widget for properties forms.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QLineEdit,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties.float_property import FloatProperty
from proteus.views.forms.properties.property_input import PropertyInput


# --------------------------------------------------------------------------
# Class: FloatPropertyInput
# Description: Float property input widget for properties forms.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class FloatPropertyInput(PropertyInput):
    """
    Float property input widget for properties forms.
    """

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 04/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> float:
        """
        Returns the value of the input widget. The value is converted to a
        float.
        """
        self.input: QLineEdit
        return float(self.input.text())

    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def validate(self) -> str | None:
        """
        Validates the input widget. Returns an error message if the input
        has errors, None otherwise.
        """
        # Perform validation to prevent non-numeric values
        text = self.input.text()
        try:
            float(text)
        except ValueError:
            return "float_property_input.validator.error"

        # Check required
        if self.property.required and (text is None or text == ""):
            return "property_input.validator.error.required"

        # Return None if the input is valid
        return None

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(property: FloatProperty, *args, **kwargs) -> QLineEdit:
        """
        Creates the input widget based on QLineEdit.
        """
        input: QLineEdit = QLineEdit()
        input.setText(str(property.value))
        return input
