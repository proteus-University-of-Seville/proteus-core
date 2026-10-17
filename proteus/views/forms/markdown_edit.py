# ==========================================================================
# File: markdown_edit.py
# Description: Markdown edit input widget for forms.
# Date: 14/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from functools import wraps
from typing import Callable

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import markdown
from PyQt6.QtGui import (
    QWheelEvent,
)
from PyQt6.QtCore import (
    QSize,
    Qt,
)
from PyQt6.QtWidgets import (
    QWidget,
    QTextEdit,
    QVBoxLayout,
    QSizePolicy,
    QPushButton,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _
from proteus.views.forms.text_edit import TextEdit


# --------------------------------------------------------------------------
# Helper widget classes (proper sizeHint overrides instead of instance
# monkey-patching, as recommended by the Riverbank documentation)
# --------------------------------------------------------------------------
class _MarkdownPreviewBox(QTextEdit):
    """Read-only preview box with a compact preferred size."""

    def sizeHint(self) -> QSize:
        return QSize(250, 100)


class _MarkdownInputBox(TextEdit):
    """Markdown input box with a compact preferred size."""

    def sizeHint(self) -> QSize:
        return QSize(250, 100)


# --------------------------------------------------------------------------
# Class: MarkdownEdit
# Description: Markdown edit input widget for forms.
# Date: 14/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MarkdownEdit(QWidget):
    """
    Markdown edit input widget for forms. It is composed by a QTextEdit
    and a QLabel. The user can interact with a button to display a preview
    of the markdown text.

    Similar to PyQt6 QLineEdit, QTextEdit, etc. It is used to retrieve the
    value of the user input.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Object initialization.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
        Object initialization.
        """
        super().__init__(*args, **kwargs)

        # Initialize widgets variables
        self.input_box: TextEdit = None
        self.display_box: QTextEdit = None
        self.mode_button: QPushButton = None

        # Create input widget
        self.create_input()

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_input(self) -> None:
        """
        Create the widgets and configure the layout.
        """

        # Display box ------------------------------------------------------
        self.display_box = _MarkdownPreviewBox()
        self.display_box.setReadOnly(True)
        self.display_box.wheelEvent = self.wheelEventDecorator(
            self.display_box.wheelEvent
        )
        self.display_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.display_box.setVisible(False)

        # Modify base font size
        font = self.display_box.font()
        font.setPointSize(font.pointSize() + 2)
        self.display_box.setFont(font)

        # Input box --------------------------------------------------------
        self.input_box = _MarkdownInputBox()
        self.input_box.wheelEvent = self.wheelEventDecorator(self.input_box.wheelEvent)
        self.input_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )

        # Modify base font size
        font = self.input_box.font()
        font.setPointSize(font.pointSize() + 2)
        self.input_box.setFont(font)

        # Mode button ------------------------------------------------------
        self.mode_button = QPushButton()
        self.mode_button.setText(_("markdown_edit.preview"))
        self.mode_button.clicked.connect(self.on_mode_button_clicked)

        # Layout setup -----------------------------------------------------
        layout = QVBoxLayout()
        layout.addWidget(self.input_box)
        layout.addWidget(self.display_box)
        layout.addWidget(self.mode_button)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    # ----------------------------------------------------------------------
    # Method     : markdown
    # Description: Returns the text of the input box.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def markdown(self) -> str:
        """
        Returns the text of the input in plain text format.
        """
        return self.input_box.toPlainText()

    # ----------------------------------------------------------------------
    # Method     : setMarkdown
    # Description: Sets the text of the input box.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setMarkdown(self, text: str) -> None:
        """
        Sets the text in plain text format to the input box.
        """
        self.input_box.setPlainText(text)

    # ----------------------------------------------------------------------
    # Method     : setEnabled
    # Description: Sets the enabled state of the inputs widget.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setEnabled(self, enabled: bool) -> None:
        """
        Sets the input to enabled or disabled state modifying the browse
        button.
        """
        self.input_box.setEnabled(enabled)

    # ======================================================================
    # Slots (connected to signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Slot       : on_mode_button_clicked
    # Description: Slot connected to the mode button clicked signal.
    # Date       : 14/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def on_mode_button_clicked(self) -> None:
        """
        Slot connected to the mode button clicked signal.
        """
        # Enter edit mode
        if self.display_box.isVisible():
            self.display_box.setVisible(False)
            self.input_box.setVisible(True)
            self.mode_button.setText(_("markdown_edit.preview"))
        # Enter preview mode
        else:
            text = self.input_box.toPlainText()
            converted_text: str = markdown.markdown(
                text,
                extensions=[
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.codehilite",
                    "markdown.extensions.tables",
                    "markdown.extensions.toc",
                ],
            )

            self.display_box.setHtml(converted_text)
            self.display_box.setVisible(True)
            self.input_box.setVisible(False)
            self.mode_button.setText(_("markdown_edit.edit"))

    # ======================================================================
    # Private and overriden methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : wheelEventDecorator
    # Description: Decorator to handle the wheel event to zoom in and out
    # Date       : 01/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    # TODO: Consider synchronizing scroll events between input and display boxes
    def wheelEventDecorator(self, wheelEventMethod: Callable) -> None:
        """
        Decorate wheel event to zoom in and out the text and display boxes
        when the control key and the mouse wheel are used. Modify the font
        size of the text at the same time to keep the same size.

        This method decorates QTextEdit and QPlainTextEdit wheelEvent methods
        to avoid inconsistencies in font sizes between both widgets due to
        default keybinding implementation in those widgets.
        """

        @wraps(wheelEventMethod)
        def wrapper(e: QWheelEvent) -> None:
            if e.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if e.angleDelta().y() > 0:
                    self.input_box.zoomIn(1)
                    self.display_box.zoomIn(1)
                else:
                    self.input_box.zoomOut(1)
                    self.display_box.zoomOut(1)
            else:
                wheelEventMethod(e)

        return wrapper


    # ----------------------------------------------------------------------
    # Method     : setFocus
    # Description: Sets the mouse focus.
    # Date       : 14/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setFocus(self) -> None:
        """
        Sets the mouse focus to the input box.
        """
        self.input_box.setFocus()