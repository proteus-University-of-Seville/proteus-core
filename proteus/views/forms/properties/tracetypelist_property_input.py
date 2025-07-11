# ==========================================================================
# File: tracetypelist_property_input.py
# Description: Trace type list input widget for properties forms.
# Date: 20/11/2024
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

from PyQt6.QtWidgets import QSizePolicy

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties import TraceTypeListProperty
from proteus.controller.command_stack import Controller
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.items.item_list_edit import ItemListEdit


# --------------------------------------------------------------------------
# Class: TraceTypeListPropertyInput
# Description: Trace type list input widget for properties forms.
# Date: 20/11/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class TraceTypeListPropertyInput(PropertyInput):
    """
    Class list input widget for properties forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 20/11/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> List:
        """
        Returns the value of the input widget. The value is converted to a
        list.
        """
        self.input: ItemListEdit
        return self.input.items()

    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 20/11/2024
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
    # Date       : 20/11/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(
        property: TraceTypeListProperty, controller: Controller, *args, **kwargs
    ) -> ItemListEdit:
        """
        Creates the input widget based on PROTEUS ObjectListEdit.
        """
        # Get project and property classes
        project_trace_types = controller.get_project_available_trace_types()
        property_trace_types = property.value

        input: ItemListEdit = ItemListEdit(candidates=project_trace_types)
        input.setItems(property_trace_types)
        input.item_list.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        return input
