# ==========================================================================
# File: unit_property_input.py
# Description: Unit property input widget for properties forms.
# Date: 19/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties.unit_property import UnitProperty, Measurement
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.measurement_edit import MeasurementEdit

# --------------------------------------------------------------------------
# Class: UnitPropertyInput
# Description: Unit property input widget for properties forms.
# Date: 19/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class UnitPropertyInput(PropertyInput):
    """
    Unit property input widget for properties forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 19/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> Measurement:
        """
        Returns the value of the input widget. The value is converted to a
        Measurement object.
        """
        self.input: MeasurementEdit
        value, unit = self.input.measurement()
        return Measurement(value=float(value), unit=unit)
    
    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 19/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def validate(self) -> str | None:
        """
        Validates the input widget. Returns an error message if the input
        has errors, None otherwise.
        """
        # Perform validation to prevent non-numeric values
        value, _ = self.input.measurement()
        try:
            float(value)
        except ValueError:
            return "unit_property_input.validator.value.error"

        # Check required
        if self.property.required and (value is None or value == ""):
            return "property_input.validator.error.required"

        # Return None if the input is valid
        return None
    
    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 19/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(property: UnitProperty, *args, **kwargs) -> MeasurementEdit:
        """
        Creates the input widget based on MeasurementEdit custom widget.
        """
        input: MeasurementEdit = MeasurementEdit(property.units)
        input.setMeasurement(property.value.value, property.value.unit)
        return input
        

