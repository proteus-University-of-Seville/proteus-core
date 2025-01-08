# ==========================================================================
# File: property_input_factory.py
# Description: Property input to handle object and project properties forms
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from datetime import date
from abc import ABC, abstractmethod

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.controller.command_stack import Controller
from proteus.model.properties.property import Property
from proteus.model.properties.code_property import ProteusCode
from proteus.application.utils.abstract_meta import AbstractObjectMeta
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.views.components.dialogs.base_dialogs import MessageBox

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: PropertyInput
# Description: Implementation of a property input widget that wraps a
#              property input widget and adds a label to display errors.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class PropertyInput(QWidget, ABC, metaclass=AbstractObjectMeta):
    """
    Property input widget that wraps a property input widget. Adds a label
    to display errors and a checkbox to edit the inmutable property if the
    property is inmutable.
    """

    def __init__(
        self, property: Property, controller: Controller = None, element_id: ProteusID = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Initialize variables
        self.controller: Controller = controller
        self.element_id: ProteusID = element_id
        self.wrap_in_group_box: bool = False

        # Initialize input widget by calling the abstract method
        self.input: QWidget = self.create_input(property, controller, element_id)
        self.property: Property = property

        self.input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Create the component
        self.create_component()

    # ======================================================================
    # Component setup (creation) methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Creates the component.
    # Date       : 31/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Creates the dialog input component. It creates a layout using the
        input widget, error label and inmutable checkbox (if property is
        inmutable). Adds the property tooltip if any.
        """
        # Initialize error label -------------------------
        self.error_label: QLabel = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        # Set property tooltip ---------------------------
        if self.property.tooltip and self.property.tooltip != "":
            self.setToolTip(
                _(
                    f"archetype.tooltip.{self.property.tooltip}",
                    alternative_text=self.property.tooltip,
                )
            )

        # Input layout -----------------------------------
        # Input layout is an horizontal layout that contains the input
        # widget and the inmutable checkbox if necessary
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.input)

        # Inmutable checkbox setup - input widget is disabled by create_inmutable_checkbox
        self.inmutable_checkbox: QCheckBox = self.create_inmutable_checkbox()
        if self.inmutable_checkbox:
            horizontal_layout.addWidget(self.inmutable_checkbox)
            horizontal_layout.setAlignment(self.inmutable_checkbox, Qt.AlignmentFlag.AlignTop)

        # Vertical main layout ---------------------------
        vertical_layout = QVBoxLayout()
        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(self.error_label)
        self.setLayout(vertical_layout)

    # ----------------------------------------------------------------------
    # Method     : create_inmutable_checkbox
    # Description: Creates the inmutable checkbox.
    # Date       : 31/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_inmutable_checkbox(self) -> QCheckBox | None:
        """
        Creates the inmutable checkbox if the property is inmutable.

        By default, the inmutable checkbox is checked and the input is
        disabled.
        """
        # Check if property is Property class and inmutable is True
        if isinstance(self.property, Property):
            inmutable: bool = self.property.inmutable
            if inmutable:

                # Create the inmutable checkbox
                inmutable_checkbox: QCheckBox = QCheckBox()
                inmutable_checkbox.setChecked(True)
                inmutable_checkbox.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                inmutable_checkbox.stateChanged.connect(self._update_enabled)

                # Set the icon
                icon: QIcon = Icons().icon(
                    ProteusIconType.App, "inmutable-property-edit-disabled"
                )
                inmutable_checkbox.setIcon(icon)

                # Set the checkbox tooltip
                inmutable_checkbox.setToolTip(
                    _("property_input.inmutable_checkbox_tooltip")
                )

                # Disable the input widget
                self.input.setEnabled(False)

                return inmutable_checkbox
        return None

    # ======================================================================
    # Public methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : has_errors
    # Description: Returns true if the input has errors, false otherwise.
    # Date       : 04/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def has_errors(self) -> bool:
        """
        Returns true if the input has errors, false otherwise. If the input
        has errors, the error label will be shown.
        """
        error: str = self.validate()
        if error:
            error_msg: str = _(error)
            self.error_label.setText(error_msg)
            self.error_label.show()
            return True
        else:
            self.error_label.hide()
            return False

    # ======================================================================
    # Abstract methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : get_value (abstract)
    # Description: Returns the value of the input widget.
    # Date       : 04/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @abstractmethod
    def get_value(self) -> str | int | float | bool | date | list | ProteusCode:
        """
        Returns the value of the input widget. The value is converted to a
        string.
        """
        pass

    # ----------------------------------------------------------------------
    # Method     : validate (abstract)
    # Description: Validates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @abstractmethod
    def validate(self) -> str | None:
        """
        Validates the input widget. Returns an error message if the input
        has errors, None otherwise.
        """
        pass

    # ----------------------------------------------------------------------
    # Method     : create_input (abstract)
    # Description: Creates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def create_input(property: Property, *args, **kwargs) -> QWidget:
        """
        Creates the input widget based on the property type.
        """
        pass

    # ======================================================================
    # Slots
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_enabled (slot)
    # Description: Updates the enabled state of the input widget.
    # Date       : 02/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _update_enabled(self, check_state: Qt.CheckState) -> None:
        """
        Updates the enabled state of the input widget.

        Only works for Property class properties.

        :param check_state: Check state of the inmutable checkbox.
        """
        # Check the state of the checkbox
        checked: bool = check_state == Qt.CheckState.Checked.value

        # Update the enabled state of the input widget
        self.input.setEnabled(not checked)

        # Update check box icon
        if self.inmutable_checkbox:
            icon_str = (
                "inmutable-property-edit-disabled"
                if checked
                else "inmutable-property-edit-enabled"
            )

            icon: QIcon = Icons().icon(ProteusIconType.App, icon_str)
            self.inmutable_checkbox.setIcon(icon)

        # Trigger inmutable property warning
        if not checked:
            MessageBox.warning(
                _("property_input.inmutable_property_warning.title"),
                _("property_input.inmutable_property_warning.text"),
            )


    # ----------------------------------------------------------------------
    # Method     : setKeyboardFocus
    # Description: Set the keyboard focus to the input widget.
    # Date       : 14/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setKeyboardFocus(self):
        """
        Set the mouse/keyboard focus to the input widget.
        """
        try:
            # Set the mouse/keyboard focus
            # Solution for mouse focus: https://stackoverflow.com/a/35765436/17947088
            QTimer.singleShot(0, self.input.setFocus)
            
        except Exception as e:
            log.error(f"Error setting keyboard focus: {e}")
            pass
