# ==========================================================================
# File: descriptive_list_edit.py
# Description: PROTEUS descriptive list form input widget.
# Date: 05/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QSizePolicy,
    QHBoxLayout,
    QListWidget,
    QPlainTextEdit,
    QListWidgetItem,
    QAbstractItemView,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: DescriptiveListEdit
# Description: Descriptive list form input widget.
# Date: 05/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DescriptiveListEdit(QWidget):
    """
    Descriptive list form input widget. It is meant to replace combo boxes
    when the data wants to be displayed along additional information.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor.
        """
        super().__init__(*args, **kwargs)

        # Widgets
        self.list_widget: QListWidget = None
        self.info_box: QPlainTextEdit = None

        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Creates the input widget.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the widgets and configure the layout.
        """

        # Widgets creation --------------------------------------------------
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.list_widget.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        # NOTE: Recomended in https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html
        self.list_widget.sizeHint = lambda: QSize(0, 100)

        # Connect signals
        self.list_widget.currentItemChanged.connect(self._update_info_box)

        self.info_box = QPlainTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        # NOTE: Recomended in https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html
        self.info_box.sizeHint = lambda: QSize(0, 0)

        # Layouts -----------------------------------------------------------
        layout = QHBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.info_box)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    # ----------------------------------------------------------------------
    # Method     : addItem
    # Description: Adds an item to the list.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_item(self, text: str, user_data: str, information: str = "") -> None:
        """
        Adds an item to the list.

        :param text: The text to display.
        :param user_data: The user data.
        :param information: The information to display.
        """
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, user_data)
        item.setData(Qt.ItemDataRole.ToolTipRole, information)
        self.list_widget.addItem(item)

    # ----------------------------------------------------------------------
    # Method     : current_item
    # Description: Returns the current item.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def current_data(self) -> str | None:
        """
        Returns the current item data.

        :return: The current item data.
        """
        selected_item = self.list_widget.currentItem()
        if selected_item is not None:
            return selected_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    # ----------------------------------------------------------------------
    # Method     : set_current_item
    # Description: Sets the current item.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def set_current_item(self, user_data: str) -> None:
        """
        Sets the current item based on the given user data.

        :param user_data: The user data.
        """
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == user_data:
                self.list_widget.setCurrentItem(item)
                break
        
    # ======================================================================
    # Connected slots
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : _update_info_box
    # Description: Updates the information box with the selected item data.
    # Date       : 05/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _update_info_box(self) -> None:
        """
        Updates the information box with the selected item data.
        """
        selected_item = self.list_widget.currentItem()
        if selected_item is not None:
            self.info_box.setPlainText(selected_item.data(Qt.ItemDataRole.ToolTipRole))

    
