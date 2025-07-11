# ==========================================================================
# File: enum_property_input.py
# Description: Enum property input widget for properties forms.
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
    QComboBox,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _
from proteus.model.properties.enum_property import EnumProperty
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.descriptive_list_edit import DescriptiveListEdit



# --------------------------------------------------------------------------
# Class: EnumPropertyInput
# Description: Enum property input widget for properties forms.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class EnumPropertyInput(PropertyInput):
    """
    Enum property input widget for properties forms.
    """

    def __init__(self, property: EnumProperty, *args, **kwargs):
        super().__init__(property, *args, **kwargs)

        if property.valueTooltips:
            self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 04/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> str:
        """
        Returns the value of the input widget. The value is converted to a
        enum.
        """
        self.input: QComboBox | DescriptiveListEdit

        if isinstance(self.input, QComboBox):
            return self.input.currentData()
        else:
            return self.input.current_data()

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

        Checks if the current data in valid. If the data is not valid it
        may indicate that the combobox was not initialized correctly.
        """

        if self.get_value() is None:
            return "property_input.validator.error.required"

        return None

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(property: EnumProperty, *args, **kwargs) -> QComboBox | DescriptiveListEdit:
        """
        Creates the input widget based on QComboBox.
        """
        input: QComboBox | DescriptiveListEdit
        choices = property.get_choices_as_list()

        # Create the property input based un valueTooltips attribute
        # NOTE: Choice tooltip is found using the convention:
        #       archetype.enum_choices.tooltip.<property_name>.<choice>
        if property.valueTooltips:
            input = DescriptiveListEdit()
            for choice in choices:
                input.add_item(
                    _(f"archetype.enum_choices.{choice}", alternative_text=choice),
                    choice,
                    _(f"archetype.enum_choices.tooltip.{property.name}.{choice}", alternative_text=""),
                )
            input.set_current_item(property.value)
        else:
            input = QComboBox()
            for choice in choices:
                input.addItem(
                    _(f"archetype.enum_choices.{choice}", alternative_text=choice),
                    choice,
                )
            input.setCurrentIndex(input.findData(property.value))

        return input
