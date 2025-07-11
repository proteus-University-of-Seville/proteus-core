# ==========================================================================
# File: trace_input.py
# Description: Trace input widget for properties forms.
# Date: 25/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.model.object import Object
from proteus.model.properties import TraceProperty
from proteus.controller.command_stack import Controller
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.items.objects_list_edit import ObjectsListEdit

# Module configuration
log = logging.getLogger(__name__)  # Logger

# --------------------------------------------------------------------------
# Class: TraceInput
# Description: Trace input widget for properties forms.
# Date: 25/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class TraceInput(PropertyInput):
    """
    Trace input widget for properties forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 25/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> List:
        """
        Returns the value of the input widget. The value is converted to a
        list.
        """
        self.input: ObjectsListEdit
        return self.input.items()

    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 25/10/2023
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
    # Date       : 25/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(
        property: TraceProperty,
        controller: Controller,
        element_id: ProteusID,
        *args,
        **kwargs
    ) -> ObjectsListEdit:
        """
        Creates the input widget based on PROTEUS ObjectListEdit.
        """

        # Candidates
        candidates_objects: List[Object] = controller.get_objects(
            classes=property.acceptedTargets
        )

        # Filter candidates by excluded targets (classes), element_id
        candidates = [
            obj.id
            for obj in candidates_objects
            if not any(
                excluded_class in obj.classes
                for excluded_class in property.excludedTargets
            )
            and obj.id != element_id
        ]

        input = ObjectsListEdit(
            controler=controller,
            candidates=candidates,
            item_limit=property.maxTargetsNumber,
        )
        
        # Set traced objects
        traced_objects: List[Object] = []
        for trace in property.value:
            # Discard traces to non-existing objects
            try:
                item = controller.get_element(trace)
                traced_objects.append(item)
            except Exception as e:
                log.error(f"Error getting traced object '{trace}': {e}")

        input.setItems(traced_objects)

        return input
