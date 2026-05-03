# ==========================================================================
# File: style_helpers.py
# Description: Helpers for theming-friendly widget styling.
# Date: 03/05/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Any

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QWidget


# --------------------------------------------------------------------------
# Function: set_styled_property
# --------------------------------------------------------------------------
def set_styled_property(widget: QWidget, name: str, value: Any) -> None:
    """
    Set a Qt dynamic property used in QSS selectors and trigger a
    re-evaluation of the active stylesheet so the new value takes effect.

    Property-based QSS selectors like ``QLabel[descriptionState="empty"]``
    are NOT re-applied automatically when ``QWidget.setProperty`` changes
    the value. The canonical fix from the Qt docs is to unpolish and
    polish the widget after the property change. This helper bundles
    those three calls so call sites stay terse and the right pattern is
    the easy path.

    :param widget: Target widget.
    :param name: Property name (must match the bracketed name in the QSS
        selector — e.g. ``"descriptionState"``).
    :param value: New property value (must match the bracketed value in
        the QSS selector — e.g. ``"empty"`` or ``"filled"``).
    """
    widget.setProperty(name, value)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
