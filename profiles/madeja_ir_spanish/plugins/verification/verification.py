# ==========================================================================
# File: verification.py
# Description: PyQT6 verification class
# Date: 25/03/2025
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

from PyQt6.QtCore import pyqtSlot

# --------------------------------------------------------------------------
# Plugin imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Proteus imports
# --------------------------------------------------------------------------

from proteus.model.abstract_object import ProteusState
from proteus.views.components.abstract_component import ProteusComponent
from proteus.model.properties import MarkdownProperty, TimeProperty, DateProperty
from proteus.application.events import RequiredSaveActionEvent

# Module configuration
log = logging.getLogger(__name__)  # Logger

# Constants
VERIFICATION_CATEGORY = "ai_verification"
VERIFICATION_PROPERTY_DATE_NAME = "ai_verification_date"
VERIFICATION_PROPERTY_TIME_NAME = "ai_verification_time"
VERIFICATION_PROPERTY_OUTPUT_NAME = "ai_verification_output"


# --------------------------------------------------------------------------
# Class: VerificationManager
# Description: Verification manager class
# Date: 25/03/2025
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class VerificationManager(ProteusComponent):

    @pyqtSlot(str, str)
    def store_verification(self, id: str, verification_output: str) -> None:

        # Create the verification properties
        current_date_property = DateProperty(
            name=VERIFICATION_PROPERTY_DATE_NAME,
            category=VERIFICATION_CATEGORY,
            inmutable=True,
        )
        current_time_property = TimeProperty(
            name=VERIFICATION_PROPERTY_TIME_NAME,
            category=VERIFICATION_CATEGORY,
            inmutable=True,
        )
        current_output_property = MarkdownProperty(
            name=VERIFICATION_PROPERTY_OUTPUT_NAME,
            category=VERIFICATION_CATEGORY,
            inmutable=True,
            value=verification_output,
        )

        # Get the object and replace the properties, if they already exist it will be like updating them
        current_object = self._controller.get_element(id)
        current_object.properties[current_date_property.name] = current_date_property
        current_object.properties[current_time_property.name] = current_time_property
        current_object.properties[current_output_property.name] = current_output_property

        current_object.state = ProteusState.DIRTY

        # Trigger required save event
        RequiredSaveActionEvent().notify()
