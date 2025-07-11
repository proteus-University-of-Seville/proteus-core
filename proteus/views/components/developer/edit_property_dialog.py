# ==========================================================================
# File: edit_property_dialog.py
# Description: module for the PROTEUS edit property dialog
# Date: 17/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Iterable

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QLabel,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QLineEdit,
)

# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.views.components.developer import XML_PROBLEMATIC_CHARS, create_error_label
from proteus.application.resources.translator import translate as _
from proteus.views.components.dialogs.base_dialogs import ProteusDialog
from proteus.controller.command_stack import Controller
from proteus.views.forms.boolean_edit import BooleanEdit
from proteus.views.forms.properties.property_input_factory import (
    PropertyInputFactory,
    PropertyInput,
)
from proteus.model.properties.property_factory import PropertyFactory
from proteus.model.object import Object
from proteus.model.properties import (
    Property,
    MarkdownProperty,
    EnumProperty,
    TraceProperty,
)


# --------------------------------------------------------------------------
# Class: EditPropertyDialog
# Description: PyQT6 dialog component for the PROTEUS edit property dialog
# Date: 16/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class EditPropertyDialog(ProteusDialog):
    """
    EditPropertyDialog provides a dialog for editing a property meta-model.

    Since properties are inmutable objects, the dialog will return a new
    property with the updated values. It is important to note that editing
    a property may create inconsistencies between the value and its attributes.
    This is a developer's responsibility.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 16/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self,
        object: Object,
        property: Property,
        invalid_property_names: Iterable[str],
        *args,
        **kwargs
    ) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component.
        """
        super(EditPropertyDialog, self).__init__(*args, **kwargs)

        self.object = object
        self._property: Property | TraceProperty | EnumProperty = property
        self.invalid_property_names = invalid_property_names

        # Return value
        self.new_property = None

        # General properties attributes widgets
        self.name_input: QLineEdit
        self.category_input: QLineEdit
        self.tooltip_input: QLineEdit
        self.required_input: BooleanEdit
        self.inmutable_input: BooleanEdit
        self.value_input: PropertyInput

        # Specific property attributes widgets
        self.choices_input: QLineEdit  # EnumProperty
        self.value_tooltips_input: BooleanEdit  # EnumProperty
        self.acceptedTargets_input: QLineEdit  # TraceProperty
        self.excludedTargets_input: QLineEdit
        self.type_input: QLineEdit
        self.max_targets_number_input: QLineEdit

        # Error labels
        self.name_error_label: QLabel = create_error_label()
        self.general_error_label: QLabel = create_error_label()

        # Create the dialog
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component
    # Date       : 17/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component
        """
        # Dialog general properties -------------------------------------------
        self.setWindowTitle(_("edit_property_dialog.title"))

        # Property attributes -------------------------------------------------
        form_layout: QFormLayout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setText(self._property.name)

        self.category_input = QLineEdit()
        self.category_input.setText(self._property.category)

        self.tooltip_input = QLineEdit()
        self.tooltip_input.setText(self._property.tooltip)

        self.required_input = BooleanEdit(_("add_property_dialog.label.required"))
        self.required_input.setChecked(self._property.required)

        self.inmutable_input = BooleanEdit(_("add_property_dialog.label.inmutable"))
        self.inmutable_input.setChecked(self._property.inmutable)

        # Add widgets to the form layout ---------------------------------------
        form_layout.addWidget(self.general_error_label)
        form_layout.addRow("name", self.name_input)
        form_layout.addWidget(self.name_error_label)
        form_layout.addRow("category", self.category_input)
        form_layout.addRow("tooltip", self.tooltip_input)
        form_layout.addRow("required", self.required_input)
        form_layout.addRow("inmutable", self.inmutable_input)

        if isinstance(self._property, EnumProperty):
            self._create_enum_property_inputs(form_layout)

        elif isinstance(self._property, TraceProperty):
            self._create_trace_property_inputs(form_layout)

        # Property input widget -----------------------------------------------
        self._create_value_input(form_layout)

        # Add the form layout to the dialog ------------------------------------
        self.set_content_layout(form_layout)

        # Set the accept button text -------------------------------------------
        self.accept_button.setText(_("dialog.accept_button"))
        self.accept_button.clicked.connect(self.accept_button_clicked)

    def _create_enum_property_inputs(self, form_layout: QFormLayout) -> None:
        """
        Create the specific inputs for an EnumProperty
        """
        self.choices_input = QLineEdit()
        self.choices_input.setText(self._property.choices)

        self.value_tooltips_input = BooleanEdit("valueTooltips")
        self.value_tooltips_input.setChecked(self._property.valueTooltips)

        form_layout.addRow("choices", self.choices_input)
        form_layout.addRow("valueTooltips", self.value_tooltips_input)

    def _create_trace_property_inputs(self, form_layout: QFormLayout) -> None:
        """
        Create the specific inputs for a TraceProperty
        """
        self.acceptedTargets_input = QLineEdit()
        self.acceptedTargets_input.setText(
            " ".join([tag for tag in self._property.acceptedTargets])
        )
        self.excludedTargets_input = QLineEdit()
        self.excludedTargets_input.setText(
            " ".join([tag for tag in self._property.excludedTargets])
        )
        self.type_input = QLineEdit()
        self.type_input.setText(self._property.traceType)
        self.max_targets_number_input = QLineEdit()
        self.max_targets_number_input.setText(str(self._property.maxTargetsNumber))

        form_layout.addRow("acceptedTargets", self.acceptedTargets_input)
        form_layout.addRow("excludedTargets", self.excludedTargets_input)
        form_layout.addRow("type", self.type_input)
        form_layout.addRow("maxTargetsNumber", self.max_targets_number_input)

    def _create_value_input(self, form_layout: QFormLayout) -> None:
        """
        Create the input widget for the property value
        """
        # Create the property input widget and label
        self.value_input: PropertyInput = PropertyInputFactory.create(
            self._property, element_id=self.object.id, controller=self._controller
        )

        # If the property is inmutable and the checkbox is created, remove it
        if self.value_input.inmutable_checkbox:
            self.value_input.inmutable_checkbox.stateChanged.disconnect()
            self.value_input.inmutable_checkbox.setChecked(False)
            self.value_input.inmutable_checkbox.hide()
            self.value_input.input.setEnabled(True)

        # NOTE: Special case for EnumProperty, propertyInput is replaced by a
        # QLineEdit widget
        if isinstance(self._property, EnumProperty):
            self.value_input = QLineEdit()
            self.value_input.setText(self._property.value)

        # Traces and MarkdownProperty are wrapped in a group box
        if isinstance(self._property, (TraceProperty, MarkdownProperty)):
            group_box: QGroupBox = QGroupBox()
            group_box.setTitle("value")
            group_box_layout: QVBoxLayout = QVBoxLayout()
            group_box_layout.addWidget(self.value_input)
            group_box_layout.setContentsMargins(0, 0, 0, 0)
            group_box.setLayout(group_box_layout)

            form_layout.addRow(group_box)
        else:
            # Add the input field widget and label to the category layout
            form_layout.addRow("value", self.value_input)

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : accept_button_clicked
    # Description: Slot method to accept the dialog
    # Date       : 17/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def accept_button_clicked(self) -> None:
        """
        Slot method to accept the dialog
        """

        def attribute_input_has_errors(input: QLineEdit) -> bool:
            if any(char in input.text().strip() for char in XML_PROBLEMATIC_CHARS):
                self.general_error_label.setText(
                    _(
                        "edit_property_dialog.error.invalid_chars_present",
                        " ".join(XML_PROBLEMATIC_CHARS),
                    )
                )
                self.general_error_label.show()
                return True
            else:
                self.general_error_label.hide()
                return

        # Name must be
        name: str = self.name_input.text().strip()
        if name in self.invalid_property_names or not name:
            self.name_error_label.setText(
                _("edit_property_dialog.error.duplicated_or_empty_name", name)
            )
            self.name_error_label.show()
            return
        else:
            self.name_error_label.hide()

        # Validate the attribute inputs ---------------------------------------

        property_input_has_errors: bool = False
        if not isinstance(self._property, EnumProperty):
            property_input_has_errors = self.value_input.has_errors()

        if (
            attribute_input_has_errors(self.name_input)
            or attribute_input_has_errors(self.category_input)
            or attribute_input_has_errors(self.tooltip_input)
            or property_input_has_errors
        ):
            return

        # EnumProperty specific attributes
        if isinstance(self._property, EnumProperty):
            if attribute_input_has_errors(self.choices_input):
                return

        # TraceProperty specific attributes
        if isinstance(self._property, TraceProperty):
            if (
                attribute_input_has_errors(self.acceptedTargets_input)
                or attribute_input_has_errors(self.excludedTargets_input)
                or attribute_input_has_errors(self.type_input)
            ):
                return

            max_targets_number_str: str = self.max_targets_number_input.text()
            if not max_targets_number_str.isdigit() and max_targets_number_str != "-1":
                self.general_error_label.setText(
                    _("edit_property_dialog.error.invalid_max_targets_number_value")
                )
                self.general_error_label.show()
                return
            elif int(max_targets_number_str) <= 0 and int(max_targets_number_str) != -1:
                self.general_error_label.setText(
                    _("edit_property_dialog.error.invalid_max_targets_number_value")
                )
                self.general_error_label.show()
                return
            else:
                self.general_error_label.hide()

        # Create the new property, check if any attribute has changed --------

        # NOTE: Special case for EnumProperty, the value is a string
        if isinstance(self._property, EnumProperty):
            value_has_changed: bool = (
                self._property.value != self.value_input.text().strip()
            )
        else:
            value_has_changed: bool = (
                self._property.value != self.value_input.get_value()
            )

        attributes_have_changed: bool = (
            self._property.name != name
            or self._property.category != self.category_input.text().strip()
            or self._property.tooltip != self.tooltip_input.text().strip()
            or self._property.required != self.required_input.checked()
            or self._property.inmutable != self.inmutable_input.checked()
            or value_has_changed
        )

        if isinstance(self._property, EnumProperty):
            attributes_have_changed = (
                attributes_have_changed
                or self._property.choices != self.choices_input.text().strip()
                or self._property.valueTooltips != self.value_tooltips_input.checked()
            )

        if isinstance(self._property, TraceProperty):
            attributes_have_changed = (
                attributes_have_changed
                or self._property.acceptedTargets
                != self.acceptedTargets_input.text().split()
                or self._property.excludedTargets
                != self.excludedTargets_input.text().split()
                or self._property.traceType != self.type_input.text().strip()
                or self._property.maxTargetsNumber
                != int(self.max_targets_number_input.text())
            )

        # If the attributes have changed, create the new property ------------
        if attributes_have_changed:
            element_tagname: str = self._property.element_tagname
            property_class: type = PropertyFactory.propertyFactory[element_tagname]

            if isinstance(self._property, EnumProperty):
                self.new_property = property_class(
                    name=name,
                    category=self.category_input.text().strip(),
                    tooltip=self.tooltip_input.text().strip(),
                    required=self.required_input.checked(),
                    inmutable=self.inmutable_input.checked(),
                    value=self.value_input.text().strip(),
                    valueTooltips=self.value_tooltips_input.checked(),
                    choices=self.choices_input.text().strip(),
                )
            elif isinstance(self._property, TraceProperty):
                self.new_property = property_class(
                    name=name,
                    category=self.category_input.text().strip(),
                    tooltip=self.tooltip_input.text().strip(),
                    required=self.required_input.checked(),
                    inmutable=self.inmutable_input.checked(),
                    value=self.value_input.get_value(),
                    acceptedTargets=self.acceptedTargets_input.text().split(),
                    excludedTargets=self.excludedTargets_input.text().split(),
                    traceType=self.type_input.text().strip(),
                    maxTargetsNumber=int(self.max_targets_number_input.text()),
                )
            else:
                self.new_property = property_class(
                    name=name,
                    category=self.category_input.text().strip(),
                    tooltip=self.tooltip_input.text().strip(),
                    required=self.required_input.checked(),
                    inmutable=self.inmutable_input.checked(),
                    value=self.value_input.get_value(),
                )

        # Close the form window
        self.close()
        self.deleteLater()

    # ======================================================================
    # Dialog static methods
    # ======================================================================
    @staticmethod
    def edit_property(
        object: Object,
        property: Property,
        invalid_property_names: Iterable[str],
        controller: Controller,
    ) -> Property:
        """
        Edit a property and return the new property
        """
        dialog: EditPropertyDialog = EditPropertyDialog(
            object, property, invalid_property_names, controller=controller
        )
        dialog.exec()

        return dialog.new_property
