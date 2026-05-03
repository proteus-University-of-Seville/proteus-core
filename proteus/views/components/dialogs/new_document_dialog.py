# ==========================================================================
# File: new_document_dialog.py
# Description: PyQT6 new document component for the PROTEUS application
# Date: 28/05/2023
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

from proteus.model import ProteusID, PROTEUS_NAME
from proteus.model.object import Object
from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _
from proteus.views.components.dialogs.base_dialogs import ProteusDialog
from proteus.views.forms.style_helpers import set_styled_property



# --------------------------------------------------------------------------
# Class: Newdocument
# Description: PyQT6 new document component for the PROTEUS application
# Date: 28/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class NewDocumentDialog(ProteusDialog):
    """
    New document component class for the PROTEUS application. It provides a
    dialog form to create new documents from document archetypes.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 28/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Create properties to store the new document data.
        """
        super(NewDocumentDialog, self).__init__(*args, **kwargs)

        # Variables to store the component widgets
        self.archetype_combo: QComboBox = None
        self.description_content_label: QLabel = None
        self.error_label: QLabel = None

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

        # Set the window title
        self.setWindowTitle(_("new_document_dialog.title"))
        self.sizeHint = lambda: QSize(450, 0)

        # Get document archetypes
        document_archetypes: List[Object] = self._controller.get_document_archetypes()
        # Create a combo box with the document archetypes
        archetype_label: QLabel = QLabel(_("new_document_dialog.combobox.label"))
        self.archetype_combo: QComboBox = QComboBox()
        self.archetype_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        archetype: Object = None
        for archetype in document_archetypes:
            self.archetype_combo.addItem(archetype.get_property(PROTEUS_NAME).value, archetype.id)

        # Show the archetype description
        description_placeholder_label: QLabel = QLabel(
            _("new_document_dialog.archetype.description")
        )
        self.description_content_label: QLabel = QLabel()
        self.description_content_label.setWordWrap(True)

        self.accept_button.clicked.connect(self.save_button_clicked)
        self.archetype_combo.currentIndexChanged.connect(self.update_description)
        self.update_description() # First call

        # Error message label
        self.error_label: QLabel = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)

        # Add the widgets to the layout
        layout.addWidget(archetype_label)
        layout.addWidget(self.archetype_combo)
        layout.addWidget(description_placeholder_label)
        layout.addWidget(self.description_content_label)
        layout.addWidget(self.error_label)
        layout.addStretch()

        self.set_content_layout(layout)


    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================
        
    # ----------------------------------------------------------------------
    # Method     : update_description
    # Description: Update the description label with the selected archetype
    # Date       : 28/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_description(self):
        """
        Update the description label with the selected archetype description.
        """
        archetype_id: ProteusID = self.archetype_combo.currentData()
        if archetype_id:
            archetype: Object = self._controller.get_archetype_by_id(archetype_id)  

            description: str = str()
            description_prop = archetype.get_property("description")
            if description_prop is not None:
                description = description_prop.value
            
            if description == "":
                set_styled_property(
                    self.description_content_label, "descriptionState", "empty"
                )
                self.description_content_label.setText(_("new_document_dialog.archetype.description.empty"))
            else:
                set_styled_property(
                    self.description_content_label, "descriptionState", "filled"
                )
                self.description_content_label.setText(description)

    # ----------------------------------------------------------------------
    # Method     : save_button_clicked
    # Description: Save button clicked event handler
    # Date       : 29/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_button_clicked(self):
        """
        Manage the save button clicked event. It creates a new document from
        the selected archetype.
        """
        archetype_id: ProteusID = self.archetype_combo.currentData()
        if archetype_id is None:
            self.error_label.setText(
                _("new_document_dialog.error.no_archetype_selected")
            )
            return

        # Create the document
        self._controller.create_document(archetype_id)

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
    def create_dialog(controller: Controller) -> "NewDocumentDialog":
        """
        Create a new document dialog and show it
        """
        dialog = NewDocumentDialog(controller=controller)
        dialog.exec()
        return dialog
