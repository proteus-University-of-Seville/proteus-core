# ==========================================================================
# File: boolean_edit.py
# Description: Boolean edit input widget for forms.
# Date: 12/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QWidget,
    QCheckBox,
    QLabel,
    QHBoxLayout,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _


# --------------------------------------------------------------------------
# Class: _ClickableLabel
# Description: Label that emits a signal when it is clicked.
# Date: 18/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
class _ClickableLabel(QLabel):
    """
    Label that emits 'clicked' when it is clicked with the left button and it
    is enabled. Used as the text of the checkbox of a BooleanEdit.
    """

    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


# --------------------------------------------------------------------------
# Class: BooleanEdit
# Description: Boolean edit input widget for forms.
# Date: 12/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class BooleanEdit(QWidget):
    """
    Boolean edit input widget for forms. It is composed by a QCheckBox and a
    QLabel that shows the tooltip if any.

    Similar to PyQt6 QLineEdit, QTextEdit, etc. It is used to retrieve the
    value of the user input.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Object initialization.
    # Date       : 12/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, tooltip: str = "", *args, **kwargs):
        """
        Object initialization.
        """
        super().__init__(*args, **kwargs)

        # Initialize widgets variables
        self.checkbox: QCheckBox = None
        self.label: QLabel = None

        # Initialize variables
        self.tooltip_str: str = tooltip

        # Create input widget
        self.create_input()

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 12/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_input(self) -> None:
        """
        Create the widgets and configure the layout.
        """

        text: str = _(
            f"archetype.tooltip.{self.tooltip_str}",
            alternative_text=self.tooltip_str,
        )

        # Widgets creation --------------------------------------------------
        # The text is shown in a word-wrapped label instead of in the checkbox:
        # the text of a checkbox does not wrap, so a long one forces a minimum
        # width that makes the form layout move the property label above the
        # field (and cut it). Clicking the label toggles the checkbox.
        self.checkbox = QCheckBox()
        self.checkbox.setAccessibleName(text)

        self.label = _ClickableLabel(text)
        self.label.setWordWrap(True)
        self.label.clicked.connect(self.checkbox.toggle)

        # Layout setup -----------------------------------------------------
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label, 1)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    # ----------------------------------------------------------------------
    # Method     : checked
    # Description: Returns the checked state of the checkbox.
    # Date       : 12/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def checked(self) -> bool:
        """
        Returns the checked state of the checkbox.
        """
        return self.checkbox.isChecked()

    # ----------------------------------------------------------------------
    # Method     : setChecked
    # Description: Sets the checked state of the checkbox.
    # Date       : 12/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setChecked(self, checked: bool) -> None:
        """
        Sets the checked state of the checkbox.
        """
        state = Qt.CheckState.Checked if bool(checked) else Qt.CheckState.Unchecked
        self.checkbox.setCheckState(state)

    # ----------------------------------------------------------------------
    # Method     : setEnabled
    # Description: Sets the enabled state of the inputs widget.
    # Date       : 12/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setEnabled(self, enabled: bool) -> None:
        """
        Sets the input to enabled or disabled state modifying the browse
        button.
        """
        self.checkbox.setEnabled(enabled)
        self.label.setEnabled(enabled)

    # ======================================================================
    # Slots (connected to signals)
    # ======================================================================
