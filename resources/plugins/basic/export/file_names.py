# ==========================================================================
# File: file_names.py
# Description: Default names of the files and folders written by the export
#              strategies of the basic plugin.
# Date: 08/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import PROTEUS_ACRONYM, PROTEUS_NAME
from proteus.application.state.manager import StateManager
from proteus.controller.command_stack import Controller

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# Characters that cannot be used in file names (Windows is the most strict)
INVALID_FILE_NAME_CHARS: str = '<>:"/\\|?*'


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------


def document_file_name(controller: Controller) -> str:
    """
    Base name for files and folders exported from the current document: its
    acronym, or its name if it has no acronym, or the current view name if
    neither is available. Characters that cannot be used in file names are
    replaced by '_'.
    """
    name: str = ""
    document_id = StateManager().get_current_document()
    if document_id is not None:
        document = controller.get_element(document_id)
        for property_name in (PROTEUS_ACRONYM, PROTEUS_NAME):
            property = document.get_property(property_name)
            if property is not None and str(property.value).strip():
                name = str(property.value).strip()
                break

    if not name:
        name = StateManager().get_current_view() or ""

    # Control characters and trailing dots or spaces are not valid either
    name = "".join(
        "_" if char in INVALID_FILE_NAME_CHARS or ord(char) < 32 else char
        for char in name
    )
    return name.rstrip(". ") or "document"
