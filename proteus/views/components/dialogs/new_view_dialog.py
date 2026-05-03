# ==========================================================================
# File: new_view_dialog.py
# Description: PyQT6 new view dialog component for the PROTEUS application
# Date: 23/06/2023
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

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
)


# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _
from proteus.views.components.dialogs.base_dialogs import ProteusDialog
from proteus.views.forms.style_helpers import set_styled_property
from proteus.application.events import AddViewEvent


# --------------------------------------------------------------------------
# Class: NewViewDialog
# Description: PyQT6 new view dialog component for the PROTEUS application
# Date: 23/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class NewViewDialog(ProteusDialog):
    """
    New view dialog component class for the PROTEUS application. It provides a
    dialog form to create new views from xsl templates.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Create properties to store the new document data.
        """
        super(NewViewDialog, self).__init__(*args, **kwargs)

        # Variables to store the component widgets
        self.view_combo: QComboBox = None
        self.error_label: QLabel = None
        self.description_content_label: QLabel = None

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component
    # Date       : 28/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()

        # Set the dialog title and width
        self.setWindowTitle(_("new_view_dialog.title"))
        self.sizeHint = lambda: QSize(400, 0)

        # Get available xls templates to create a new view
        xls_templates: List[str] = self._controller.get_available_xslt()

        # Create a combo box with the available views
        view_label: QLabel = QLabel(_("new_view_dialog.combobox.label"))
        self.view_combo: QComboBox = QComboBox()
        self.view_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Add the view names to the combo box
        for view in xls_templates:
            view_translation: str = _(f"xslt_templates.{view}", alternative_text=view)
            self.view_combo.addItem(view_translation, view)

        # Create description labels
        self.description_content_label: QLabel = QLabel()
        self.description_content_label.setWordWrap(True)

        # Connect the buttons to the slots, combo current data is the view name
        self.accept_button.clicked.connect(
            lambda: self.accept_button_clicked(self.view_combo.currentData())
        )
        self.view_combo.currentIndexChanged.connect(self.update_description)
        self.update_description()  # First call

        # Error message label
        self.error_label: QLabel = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)

        # Add the widgets to the layout
        layout.addWidget(view_label)
        layout.addWidget(self.view_combo)
        layout.addWidget(self.description_content_label)
        layout.addWidget(self.error_label)
        layout.addStretch()

        self.set_content_layout(layout)

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_description
    # Description: Update the description label with the selected view description
    # Date       : 07/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_description(self) -> None:
        """
        Update the description label with the selected view description.
        """
        view_name: str = self.view_combo.currentData()
        if view_name:
            description: str = _(
                f"xslt_templates.description.{view_name}", alternative_text=""
            )
            if description == "":
                set_styled_property(
                    self.description_content_label, "descriptionState", "empty"
                )
                self.description_content_label.setText(
                    _("new_document_dialog.archetype.description.empty")
                )
            else:
                set_styled_property(
                    self.description_content_label, "descriptionState", "filled"
                )
                self.description_content_label.setText(description)

    # ----------------------------------------------------------------------
    # Method     : accept_button_clicked
    # Description: Save button clicked event handler
    # Date       : 29/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def accept_button_clicked(self, combo_text: str) -> None:
        """
        Manage the save button clicked event. It creates a new view from the
        selected xslt template.
        """
        if combo_text is None:
            self.error_label.setText(_("new_view_dialog.error.no_view_selected"))
            return

        if combo_text in self._state_manager.opened_views:
            self.error_label.setText(_("new_view_dialog.error.duplicated_view"))
            return

        # Trigger ADD_VIEW event notifying the new template
        AddViewEvent().notify(combo_text)

        # Close the form window
        self.close()
        self.deleteLater()

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog
    # Description: Create a new document dialog and show it
    # Date       : 05/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(controller: Controller) -> "NewViewDialog":
        """
        Create a new document dialog and show it
        """
        dialog = NewViewDialog(controller=controller)
        dialog.exec()
        return dialog
