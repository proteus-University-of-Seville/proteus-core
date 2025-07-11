# ==========================================================================
# File: classlist_property_input.py
# Description: Class list input widget for properties forms.
# Date: 06/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties import ClassListProperty
from proteus.controller.command_stack import Controller
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.items.class_edit import ClassEdit


# --------------------------------------------------------------------------
# Class: ClassListPropertyInput
# Description: Class list input widget for properties forms.
# Date: 06/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ClassListPropertyInput(PropertyInput):
    """
    Class list input widget for properties forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 06/02/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> List:
        """
        Returns the value of the input widget. The value is converted to a
        list.
        """
        self.input: ClassEdit
        return self.input.items()

    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 06/02/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def validate(self) -> str:
        """
        Validates the input widget. Returns an error message if the input
        has errors, None otherwise.
        """
        pass

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 06/02/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(
        property: ClassListProperty, controller: Controller, *args, **kwargs
    ) -> ClassEdit:
        """
        Creates the input widget based on PROTEUS ObjectListEdit.
        """
        # Get project and property classes
        project_classes = controller.get_project_available_classes()
        property_classes = property.value

        input: ClassEdit = ClassEdit(candidates=project_classes)
        input.setItems(property_classes)

        return input
