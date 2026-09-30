# ==========================================================================
# File: information_dialog.py
# Description: PyQT6 information dialog component.
# Date: 09/08/2023
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
    QVBoxLayout,
    QLabel,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_VERSION
from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _
from proteus.views.components.dialogs.base_dialogs import ProteusDialog


# --------------------------------------------------------------------------
# Class: InformationDialog
# Description: Class for the PROTEUS application information dialog.
# Date: 09/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
# NOTE: Due to the simplicity of this component, it is not necessary to
# inherit from the ProteusComponent class. It will access the translator
# singleton directly.
class InformationDialog(ProteusDialog):
    """
    Class for the PROTEUS application information dialog.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Store the page object and the controller instance.
        """
        super(InformationDialog, self).__init__(*args, **kwargs)
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component.
        """
        # Set the dialog title
        self.setWindowTitle(_("information_dialog.title"))

        # App name and version
        app_name = QLabel("PROTEUS")
        app_name.setObjectName("app_name_label")

        app_version = QLabel(PROTEUS_VERSION)
        app_version.setObjectName("app_version_label")
        app_version.setContentsMargins(0, 0, 0, 20)

        # App description
        app_description = QLabel(_("information_dialog.description.text"))
        app_description.setWordWrap(True)
        app_description.setContentsMargins(0, 0, 0, 20)

        # License
        license = QLabel(_("information_dialog.license.text"))
        license.setWordWrap(True)
        license.setContentsMargins(0, 0, 0, 20)

        # Terms of use and privacy policy
        terms_of_use = QLabel(_("information_dialog.terms_of_use.text"))
        terms_of_use.setWordWrap(True)
        terms_of_use.setContentsMargins(0, 0, 0, 20)

        # Icons8 attribution
        icons8_attribution = QLabel("Icons by <a href='https://icons8.com'>Icons8</a>")
        icons8_attribution.setOpenExternalLinks(True)
        icons8_attribution.setContentsMargins(0, 0, 0, 20)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(app_name)
        layout.addWidget(app_version)
        layout.addWidget(app_description)
        layout.addWidget(license)
        layout.addWidget(terms_of_use)
        layout.addWidget(icons8_attribution)
        layout.addStretch()

        # Buttons options
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setText(_("dialog.close_button")) # Override text
        self.reject_button.setHidden(True)

        # Set the layout
        self.set_content_layout(layout)

        self.setFixedSize(self.sizeHint())

    # ======================================================================
    # Dialog slots methods (connected to the component signals and helpers)
    # ======================================================================

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog (static)
    # Description: Handle the creation and display of the form window.
    # Date       : 09/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(controller: Controller) -> "InformationDialog":
        """
        Handle the creation and display of the form window.

        :param controller: The application controller.
        """
        # Create the form window
        form_window = InformationDialog(controller=controller)
        form_window.exec()
        return form_window
