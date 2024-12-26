# ==========================================================================
# File: property_input_factory.py
# Description: Implementation of a property input factory to handle the
#              creation of property input widgets.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel, QSizePolicy

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _

# Properties imports
from proteus.model.properties import NO_TARGETS_LIMIT
from proteus.model.properties.property import Property
from proteus.model.properties.string_property import StringProperty
from proteus.model.properties.boolean_property import BooleanProperty
from proteus.model.properties.date_property import DateProperty
from proteus.model.properties.time_property import TimeProperty
from proteus.model.properties.markdown_property import MarkdownProperty
from proteus.model.properties.integer_property import IntegerProperty
from proteus.model.properties.float_property import FloatProperty
from proteus.model.properties.enum_property import EnumProperty
from proteus.model.properties.file_property import FileProperty
from proteus.model.properties.url_property import UrlProperty
from proteus.model.properties.classlist_property import ClassListProperty
from proteus.model.properties.code_property import CodeProperty
from proteus.model.properties.trace_property import TraceProperty
from proteus.model.properties.tracetypelist_property import TraceTypeListProperty
from proteus.model.properties.unit_property import UnitProperty

# Property input imports
from proteus.views.forms.properties.trace_input import TraceInput
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.properties.string_property_input import (
    StringPropertyInput,
)
from proteus.views.forms.properties.boolean_property_input import (
    BooleanPropertyInput,
)
from proteus.views.forms.properties.date_property_input import DatePropertyInput
from proteus.views.forms.properties.time_property_input import TimePropertyInput
from proteus.views.forms.properties.markdown_property_input import (
    MarkdownPropertyInput,
)
from proteus.views.forms.properties.integer_property_input import (
    IntegerPropertyInput,
)
from proteus.views.forms.properties.float_property_input import (
    FloatPropertyInput,
)
from proteus.views.forms.properties.enum_property_input import EnumPropertyInput
from proteus.views.forms.properties.file_property_input import FilePropertyInput
from proteus.views.forms.properties.url_property_input import UrlPropertyInput
from proteus.views.forms.properties.code_property_input import CodePropertyInput
from proteus.views.forms.properties.classlist_property_input import (
    ClassListPropertyInput,
)
from proteus.views.forms.properties.tracetypelist_property_input import (
    TraceTypeListPropertyInput,
)
from proteus.views.forms.properties.unit_property_input import UnitPropertyInput

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: PropertyInputFactory
# Description: Implementation of a property input factory to handle the
#              creation of property input widgets.
# Date: 26/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class PropertyInputFactory:
    """
    Implementation of a property input factory to handle the creation of
    property input widgets.
    """

    # Map of property types to input creation functions
    property_input_map: Dict[Property, PropertyInput] = {
        TraceProperty: TraceInput,
        StringProperty: StringPropertyInput,
        DateProperty: DatePropertyInput,
        TimeProperty: TimePropertyInput,
        MarkdownProperty: MarkdownPropertyInput,
        BooleanProperty: BooleanPropertyInput,
        FloatProperty: FloatPropertyInput,
        IntegerProperty: IntegerPropertyInput,
        EnumProperty: EnumPropertyInput,
        FileProperty: FilePropertyInput,
        UrlProperty: UrlPropertyInput,
        CodeProperty: CodePropertyInput,
        ClassListProperty: ClassListPropertyInput,
        TraceTypeListProperty: TraceTypeListPropertyInput,
        UnitProperty: UnitPropertyInput,
    }

    # ----------------------------------------------------------------------
    # Method     : create
    # Description: Creates a property input widget for the given property.
    # Date       : 26/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create(
        property: Property, element_id: ProteusID = None, controller: Controller = None
    ) -> PropertyInput:
        try:
            # Retrieve the input class for the given property type or trace
            property_input_class = PropertyInputFactory.property_input_map[
                type(property)
            ]
            property_input: PropertyInput = property_input_class(
                property, controller=controller, element_id=element_id
            )
            return property_input
        except KeyError:
            log.error(f"Property input widget for {type(property)} was not found")
            return None

    # ----------------------------------------------------------------------
    # Method     : generate_label
    # Description: Generates the label for the given property.
    # Date       : 31/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    # TODO: Consider implementing this method in PropertyInput class in order
    # to allow custom label generation for each property class. Future feature.
    @staticmethod
    def generate_label(property: Property) -> QLabel:
        """
        Generates the label for the given property. The label is generated
        using the property name and checking if the property is marked as
        required.

        Required properties will have a * at the end of the label and text
        is bolded.
        """
        # Create the label
        label = QLabel()
        name = _(f"archetype.prop_name.{property.name}", alternative_text=property.name)
        label.setWordWrap(True)

        # Size policy expanding is required to center labels vertically in the form layout
        # https://stackoverflow.com/q/34644808
        # In order to avoid excessive vertical spacing between property inputs and ensure
        # consistent resizing behavior, we set the maximum height of the label based on the
        # font size height.
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        font_metrics = QFontMetrics(label.font())
        label.setMaximumHeight(font_metrics.height())

        # Check if the property is required

        if isinstance(property, TraceProperty):
            if property.maxTargetsNumber != NO_TARGETS_LIMIT:
                max_label = _("property_input.max_targets_label")
                name = f"{name} ( {max_label} {property.maxTargetsNumber} )"
        else:
            if property.required:
                label.setToolTip(_("property_input.required_tooltip"))

        # Set the label text
        label.setText(name)
        return label
