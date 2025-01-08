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

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.translator import translate as _


# logging configuration
log = logging.getLogger(__name__)


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
    """

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

        # Add widgets to the layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(_("measurement_edit.value", alternative_text="")))
        layout.addWidget(self.value_edit)
        layout.addWidget(QLabel(_("measurement_edit.unit", alternative_text="")))
        layout.addWidget(self.unit_combo)
        self.setLayout(layout)

        # Set size policy
        self.value_edit.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.unit_combo.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

    # ----------------------------------------------------------------------
    # Method     : measurement
    # Date       : 17/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def measurement(self) -> Tuple[str, str]:
        """
        Return the value and unit of the measurement.
        """
        return self.value_edit.text(), self.unit_combo.currentText()

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
