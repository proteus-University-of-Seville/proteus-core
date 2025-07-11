# ==========================================================================
# File: class_edit.py
# Description: classes list edit input for the PROTEUS application
# Date: 06/11/2024
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
from PyQt6.QtWidgets import (
    QListWidgetItem,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusClassTag
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.translator import translate as _
from proteus.views.forms.items.item_list_edit import ItemListEdit

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ClassEdit
# Description: classes list edit input for the PROTEUS application
# Date: 06/11/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ClassEdit(ItemListEdit):
    """
    Inherit from ItemListEdit and override list_item_setup method to setup
    the list item with the class tag.
    """

    # --------------------------------------------------------------------------
    # Method: list_item_setup (override)
    # Description: Setup list item
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def list_item_setup(self, list_item: QListWidgetItem, _class: ProteusClassTag):
        """
        Setup list item with class tag translation and icon.

        :param list_item: QListWidgetItem
        :param _class: proteus class tag
        """
        list_item.setData(Qt.ItemDataRole.UserRole, _class)
        list_item.setText(_(f"archetype.class.{_class}"))
        list_item.setIcon(Icons().icon(ProteusIconType.Archetype, _class))
