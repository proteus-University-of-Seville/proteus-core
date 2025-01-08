# ==========================================================================
# File: base_dialogs.py
# Description: Proteus base dialog classes and utilities
# Date: 23/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QDialog,
    QToolButton,
    QLayout,
    QMessageBox,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.views.components.abstract_component import ProteusComponent


# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ProteusDialog
# Description: Class for the PROTEUS application base dialog
# Date: 23/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ProteusDialog(QDialog, ProteusComponent):
    """
    Base class for the PROTEUS application dialogs. It may be used as super class
    for the application dialogs.

    It provides the basic structure for the application dialogs, including the
    accept/reject buttons and a corporate logo placed at the right. Content layout
    may be set using the set_content_layout method and will be placed at the left.

    Buttons variables self.accept_button and self.reject_button can be accessed in
    order to connect signals, override text, hide, disable, etc.

    Content layout is included in a QWidget named "dialog_content_widget". This allows
    to apply styles to the content background and border.

    NOTE about Modal and Non-Modal Dialogs:
    - Modal dialogs may be triggered using the exec() method. They just need a
      controller instance (controller=controller) in order to work. They block the
      application until the dialog is closed.
    - Non-Modal dialogs may be triggered using the show() method. They need a parent
      widget (parent=parent) and a controller instance (controller=controller) in order
      to work. They do not block the application until the dialog is closed.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Class constructor
    # Date: 23/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ProteusDialog, self).__init__(*args, **kwargs)

        # Variables --------------------------------

        # Buttons
        self.accept_button: QToolButton
        self.reject_button: QToolButton

        # Content
        self._content_widget: QWidget = None
        self._content_layout: QLayout = None

        # Layouts
        self._buttons_layout: QVBoxLayout
        self._dialog_layout: QHBoxLayout

        # Dialog configuration --------------------

        # Icon may be overriden by the child class
        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

        self._content_widget = QWidget()
        self._content_widget.setObjectName("dialog_content_widget")

        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.accept_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.accept_button.setText(_("dialog.accept_button"))

        self.reject_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.reject_button.setText(_("dialog.reject_button"))

        us_logo: QIcon = Icons().icon(ProteusIconType.App, "US-digital")
        us_logo_label: QLabel = QLabel()
        us_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        us_logo_label.setPixmap(us_logo.pixmap(80, 80))

        self._buttons_layout = QVBoxLayout()
        self._buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._buttons_layout.addWidget(self.accept_button)
        self._buttons_layout.addWidget(self.reject_button)
        self._buttons_layout.addStretch()
        self._buttons_layout.addWidget(us_logo_label)

        # Main layout
        self._dialog_layout = QHBoxLayout()
        self._dialog_layout.addLayout(self._buttons_layout)
        self.setLayout(self._dialog_layout)

        # Signals
        self.reject_button.clicked.connect(self.reject_button_clicked)

    # --------------------------------------------------------------------------
    # Method: set_content_layout
    # Description: Set the content layout
    # Date: 23/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_content_layout(self, layout: QLayout) -> None:
        """
        Set the content layout for the dialog. It will be placed at the left of the
        dialog. It is inserted in a QWidget named "dialog_content_widget" to allow
        applying styles to the content background and border.
        """

        assert not isinstance(
            self._content_layout, QLayout
        ), "Content layout is already set."

        self._content_widget.setLayout(layout)

        self._content_layout = layout
        self._dialog_layout.insertWidget(0, self._content_widget)


    # ----------------------------------------------------------------------
    # Method     : reject_button_clicked
    # Description: Manage the reject button clicked event. It closes the
    #              dialog.
    # Date       : 11/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def reject_button_clicked(self):
        """
        Manage the reject button clicked event. It closes the dialog.
        """
        # Close the form window without saving any changes
        self.close()
        self.deleteLater()

# --------------------------------------------------------------------------
# Class: MessageBox
# Description: Class for the PROTEUS application message box
# Date: 26/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MessageBox(QMessageBox):
    """
    Subclass of QMessageBox that provides a more consistent look and feel with the
    PROTEUS application.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Class constructor
    # Date: 26/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self, parent, *args, **kwargs):
        super(MessageBox, self).__init__(parent, *args, **kwargs)

        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

    # --------------------------------------------------------------------------
    # Method: information (static method)
    # Description: Show an information message box
    # Date: 26/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def information(title, text, informative_text="", parent=None) -> QMessageBox.StandardButton:
        """
        Show an information message box with the given title, text and informative text.
        Contains an "Accept" button (QMessageBox.StandardButton.Ok).

        :param title: message box title
        :param text: message box text
        :param informative_text: informative text
        :param parent: parent widget
        """
        msg = MessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(text)

        if informative_text != "" and informative_text is not None:
            msg.setInformativeText(informative_text)

        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        button = msg.button(QMessageBox.StandardButton.Ok)
        button.setText(_("dialog.accept_button"))

        return msg.exec()


    # --------------------------------------------------------------------------
    # Method: warning (static method)
    # Description: Show a warning message box
    # Date: 26/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def warning(title, text, informative_text="", parent=None) -> QMessageBox.StandardButton:
        """
        Show a warning message box with the given title, text and informative text.
        Contains an "Accept" button (QMessageBox.StandardButton.Ok).

        :param title: message box title
        :param text: message box text
        :param informative_text: informative text
        :param parent: parent widget
        """
        msg = MessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)

        if informative_text != "" and informative_text is not None:
            msg.setInformativeText(informative_text)

        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        button = msg.button(QMessageBox.StandardButton.Ok)
        button.setText(_("dialog.accept_button"))

        return msg.exec()


    # --------------------------------------------------------------------------
    # Method: critical (static method)
    # Description: Show a critical message box
    # Date: 26/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def critical(title, text, informative_text="", parent=None) -> QMessageBox.StandardButton:
        """
        Show a critical message box with the given title, text and informative text.
        Contains an "Accept" button (QMessageBox.StandardButton.Ok).

        :param title: message box title
        :param text: message box text
        :param informative_text: informative text
        :param parent: parent widget
        """
        msg = MessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)

        if informative_text != "" and informative_text is not None:
            msg.setInformativeText(informative_text)

        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        button = msg.button(QMessageBox.StandardButton.Ok)
        button.setText(_("dialog.close_button"))

        return msg.exec()

    # --------------------------------------------------------------------------
    # Method: question (static method)
    # Description: Show a question message box
    # Date: 26/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def question(title, text, informative_text="", parent=None) -> QMessageBox.StandardButton:
        """
        Show a question message box with the given title, text and informative text.
        Contains "Yes" and "No" buttons (QMessageBox.StandardButton.Yes and
        QMessageBox.StandardButton.No).

        :param title: message box title
        :param text: message box text
        :param informative_text: informative text
        :param parent: parent widget
        """
        msg = MessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(title)
        msg.setText(text)

        if informative_text != "" and informative_text is not None:
            msg.setInformativeText(informative_text)

        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        button_yes = msg.button(QMessageBox.StandardButton.Yes)
        button_yes.setText(_("dialog.yes_button"))
        button_no = msg.button(QMessageBox.StandardButton.No)
        button_no.setText(_("dialog.no_button"))

        return msg.exec()