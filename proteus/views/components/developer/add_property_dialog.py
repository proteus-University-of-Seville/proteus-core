# ==========================================================================
# File: add_property_dialog.py
# Description: module for the PROTEUS add property dialog
# Date: 16/10/2024
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
    QComboBox,
    QLineEdit,
)

# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.views.components.developer import XML_PROBLEMATIC_CHARS, create_error_label
from proteus.application.resources.translator import translate as _
from proteus.views.components.dialogs.base_dialogs import ProteusDialog, MessageBox
from proteus.controller.command_stack import Controller
from proteus.views.forms.boolean_edit import BooleanEdit

from proteus.model.properties import (
    Property,
    StringProperty,
    BooleanProperty,
    DateProperty,
    TimeProperty,
    MarkdownProperty,
    IntegerProperty,
    FloatProperty,
    EnumProperty,
    FileProperty,
    UrlProperty,
    ClassListProperty,
    TraceProperty,
    CodeProperty,
)

# Constants

PROPERTY_CLASSES = {
    StringProperty.__name__: StringProperty,
    BooleanProperty.__name__: BooleanProperty,
    DateProperty.__name__: DateProperty,
    TimeProperty.__name__: TimeProperty,
    MarkdownProperty.__name__: MarkdownProperty,
    IntegerProperty.__name__: IntegerProperty,
    FloatProperty.__name__: FloatProperty,
    EnumProperty.__name__: EnumProperty,
    FileProperty.__name__: FileProperty,
    UrlProperty.__name__: UrlProperty,
    ClassListProperty.__name__: ClassListProperty,
    TraceProperty.__name__: TraceProperty,
    CodeProperty.__name__: CodeProperty,
}


# --------------------------------------------------------------------------
# Class: AddPropertyDialog
# Description: PyQT6 dialog component for the PROTEUS add property dialog
# Date: 16/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class AddPropertyDialog(ProteusDialog):
    """
    AddPropertyDialog provides an interface for creating a new property
    from any of the existing property classes (stringProperty, integerProperty, etc.).

    Allows the user to set property common attributes such as name, category, tooltip,
    required and inmutable. Specific property attributed must be set in the property
    model editor.

    Dialog returns a property object.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 16/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, invalid_property_names: Iterable[str], *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component.
        """
        super(AddPropertyDialog, self).__init__(*args, **kwargs)

        self.invalid_property_names = invalid_property_names

        # Attribute widgets
        self.name_input: QLineEdit
        self.category_input: QLineEdit
        self.tooltip_input: QLineEdit
        self.required_input: BooleanEdit
        self.inmutable_input: BooleanEdit
        self.property_class_combobox: QComboBox

        # Error labels
        self.name_error_label: QLabel = create_error_label()
        self.category_error_label: QLabel = create_error_label()
        self.tooltip_error_label: QLabel = create_error_label()

        # Return value
        self.property: Property = None

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component
    # Date       : 16/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component
        """
        # Dialog general properties -------------------------------------------
        self.setWindowTitle(_("add_property_dialog.title"))

        # Property attributes -------------------------------------------------
        form_layout: QFormLayout = QFormLayout()

        self.name_input = QLineEdit()
        self.tooltip_input = QLineEdit()
        self.category_input = QLineEdit()
        self.required_input = BooleanEdit(_("add_property_dialog.label.required"))
        self.inmutable_input = BooleanEdit(_("add_property_dialog.label.inmutable"))

        form_layout.addRow("name", self.name_input)
        form_layout.addWidget(self.name_error_label)

        form_layout.addRow("category", self.category_input)
        form_layout.addWidget(self.category_error_label)

        form_layout.addRow("tooltip", self.tooltip_input)
        form_layout.addWidget(self.tooltip_error_label)

        form_layout.addRow("required", self.required_input)
        form_layout.addRow("inmutable", self.inmutable_input)

        # Property class selection --------------------------------------------
        self.property_class_combobox = QComboBox()
        self.property_class_combobox.addItems(PROPERTY_CLASSES.keys())

        form_layout.addRow(_("add_property_dialog.label.property_class"), self.property_class_combobox)

        # Property specific attributes message --------------------------------
        message_label: QLabel = QLabel(
            _("add_property_dialog.message.property_specific_attributes")
        )
        message_label.setWordWrap(True)
        message_label.setObjectName("message_label")
        form_layout.addWidget(message_label)

        # Dialog final setup -------------------------------------------------
        self.set_content_layout(form_layout)

        self.accept_button.setText(_("dialog.create_button"))
        self.accept_button.clicked.connect(self.accept_button_clicked)

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : accept_button_clicked
    # Description: Slot method to accept the dialog
    # Date       : 16/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def accept_button_clicked(self) -> None:
        """
        Slot method to accept the dialog
        """

        # Validate the attribute inputs

        name: str = self.name_input.text().strip()
        category: str = self.category_input.text().strip()
        tooltip: str = self.tooltip_input.text().strip()
        required: bool = self.required_input.checked()
        inmutable: bool = self.inmutable_input.checked()

        # Name cannot be empty or contain XML problematic characters
        if not name or any(char in name for char in XML_PROBLEMATIC_CHARS):
            self.name_error_label.setText(_("add_property_dialog.error.invalid_name"))
            self.name_error_label.show()
            return
        else:
            self.name_error_label.hide()

        # Name must be unique
        if name in self.invalid_property_names:
            self.name_error_label.setText(
                _("add_property_dialog.error.duplicated_name", name)
            )
            self.name_error_label.show()
            return
        else:
            self.name_error_label.hide()

        # Category and tooltip cannot contain XML problematic characters
        if any(char in category for char in XML_PROBLEMATIC_CHARS):
            self.category_error_label.setText(
                _("add_property_dialog.error.invalid_characters")
            )
            self.category_error_label.show()
            return
        else:
            self.category_error_label.hide()

        if any(char in tooltip for char in XML_PROBLEMATIC_CHARS):
            self.tooltip_error_label.setText(
                _("add_property_dialog.error.invalid_characters")
            )
            self.tooltip_error_label.show()
            return

        # Create the property
        property_class: type = PROPERTY_CLASSES[
            self.property_class_combobox.currentText()
        ]
        try:
            self.property = property_class(
                name=name,
                category=category,
                tooltip=tooltip,
                required=required,
                inmutable=inmutable,
            )
        except Exception as e:
            MessageBox.critical(
                self,
                _("add_property_dialog.message_box.critical.create_property"),
                str(e),
            )
            return

        # Close the form window
        self.close()
        self.deleteLater()

    # ======================================================================
    # Dialog static methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_property
    # Description: Create a new property
    # Date       : 16/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_property(
        controller: Controller, invalid_property_names: Iterable[str]
    ) -> Property:
        """
        Create a new property
        """
        dialog: AddPropertyDialog = AddPropertyDialog(
            invalid_property_names=invalid_property_names, controller=controller
        )
        dialog.exec()
        return dialog.property
