# ==========================================================================
# File: measurement_edit.py
# Description: Measurement edit input widget for forms.
# Date: 17/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Tuple, Iterable
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _


# logging configuration
log = logging.getLogger(__name__)

# Horizontal margin QLineEdit keeps at each side of its text (Qt internal
# constant, QLineEditPrivate::horizontalMargin)
LINE_EDIT_TEXT_MARGIN: int = 2


# --------------------------------------------------------------------------
# Class: MeasurementEdit
# Date: 17/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MeasurementEdit(QWidget):
    """
    Measurement edit input widget for forms. It is composed by a QLineEdit
    and a QComboBox widgets to let the user input a value and a unit.

    Similar to PyQt6 QLineEdit, QTextEdit, etc. It is used to retrieve the
    value of the user input.

    Both widgets keep a compact width: the value edit fits VALUE_CHARACTERS
    characters and the unit combo box fits its longest unit label. The
    remaining horizontal space is left empty at the right.
    """

    # Number of characters the value edit is sized for
    VALUE_CHARACTERS: int = 8

    # Space between the value edit and the unit label (pixels)
    UNIT_SPACING: int = 12

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, units: Iterable[str], *args, **kwargs):
        """
        Object initialization.
        """
        super().__init__(*args, **kwargs)

        self.units = units

        # Create widgets
        self.value_edit: QLineEdit = None
        self.unit_combo: QComboBox = None

        # Create input
        self._create_input()

    # ----------------------------------------------------------------------
    # Method     : _create_input
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _create_input(self) -> None:
        """
        Create the input widget layout. Create a QLineEdit widget for the
        value and a QComboBox widget for the unit. Label widgets are not
        displayed if no translation is found.
        """
        layout = QHBoxLayout()

        # Populate the unit combo box
        self.unit_combo = QComboBox()
        for unit in self.units:
            self.unit_combo.addItem(
                _(f"archetype.enum_units.{unit}", alternative_text=unit), unit
            )

        # Create the value edit widget
        self.value_edit = QLineEdit()

        # Add widgets to the layout, packed to the left
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(_("measurement_edit.value", alternative_text="")))
        layout.addWidget(self.value_edit)
        layout.addSpacing(self.UNIT_SPACING)
        layout.addWidget(QLabel(_("measurement_edit.unit", alternative_text="")))
        layout.addWidget(self.unit_combo)
        layout.addStretch(1)
        self.setLayout(layout)

        # Keep the natural height of single-line widgets (otherwise they grow
        # to fill the form) and a compact width: the combo box fits its
        # longest unit label, the value edit width is set in
        # _update_value_edit_width once the style sheet has been applied.
        self.value_edit.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.unit_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.unit_combo.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._update_value_edit_width()

    # ----------------------------------------------------------------------
    # Method     : _update_value_edit_width
    # Date       : 01/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _update_value_edit_width(self) -> None:
        """
        Set the value edit width to fit VALUE_CHARACTERS digits with its
        current font, frame and padding (as defined by the style sheet).
        """
        text_width = self.value_edit.fontMetrics().horizontalAdvance(
            "0" * self.VALUE_CHARACTERS
        )

        # Space taken by the frame, border and padding: the difference between
        # the widget width and the width of its text area, as computed by the
        # current style (which takes the style sheet into account)
        option = QStyleOptionFrame()
        self.value_edit.initStyleOption(option)
        text_area = self.value_edit.style().subElementRect(
            QStyle.SubElement.SE_LineEditContents, option, self.value_edit
        )
        frame_width = option.rect.width() - text_area.width()

        # QLineEdit also keeps a small margin at each side of the text and
        # needs room for the cursor
        margins = self.value_edit.textMargins()
        extra = margins.left() + margins.right() + 2 * LINE_EDIT_TEXT_MARGIN + 2

        self.value_edit.setFixedWidth(text_width + frame_width + extra)

    # ----------------------------------------------------------------------
    # Method     : showEvent / changeEvent
    # Date       : 01/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def showEvent(self, event) -> None:
        """
        Recompute the value edit width when shown, i.e. once the application
        style sheet (font size, padding) applies to the widget.
        """
        self._update_value_edit_width()
        super().showEvent(event)

    def changeEvent(self, event) -> None:
        """
        Recompute the value edit width when the font or the style changes.
        """
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._update_value_edit_width()
        super().changeEvent(event)

    # ----------------------------------------------------------------------
    # Method     : measurement
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def measurement(self) -> Tuple[str, str]:
        """
        Return the value and unit of the measurement.

        The unit is the item data (the unit key, e.g. 'day'), not the text
        shown in the combo box, which may be a translation (e.g. 'día').
        """
        return self.value_edit.text(), self.unit_combo.currentData()

    # ----------------------------------------------------------------------
    # Method     : setMeasurement
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setMeasurement(self, value: float, unit: str) -> None:
        """
        Set the value and unit of the measurement.
        """
        self.value_edit.setText(f"{value:g}")

        # Check if the unit is in the combo box, if not, set the first one
        if unit not in [
            self.unit_combo.itemData(i) for i in range(self.unit_combo.count())
        ]:
            log.error(
                f"Unit '{unit}' is not in the combo box. Setting the first one '{self.unit_combo.itemData(0)}'"
            )
            unit = self.unit_combo.itemData(0)

        self.unit_combo.setCurrentIndex(self.unit_combo.findData(unit))

    # ----------------------------------------------------------------------
    # Method     : setEnabled
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setEnabled(self, enabled: bool) -> None:
        """
        Set the enabled state of the widgets.
        """
        self.value_edit.setEnabled(enabled)
        self.unit_combo.setEnabled(enabled)
