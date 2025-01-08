# ==========================================================================
# File: item_list_edit.py
# Description: item list edit generic input for the PROTEUS application
# Date: 31/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import List, Any, Tuple, Iterable, Callable

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QLineEdit,
    QAbstractItemView,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.translator import translate as _

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ItemListEdit
# Description: item list edit generic input for the PROTEUS application
# Date: 31/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ItemListEdit(QWidget):
    """
    Generic item list edit widget. It allows the user to add and remove items
    from a list. The items are displayed in a QListWidget and can be moved.

    Create a new class that inherits from this one and override the list_item_setup
    method to customize the appearance of the items in the list and the item picker
    dialog.
    """

    # Signals
    itemsChanged = pyqtSignal()

    # ----------------------------------------------------------------------
    # Method: __init__
    # Description: Initializes the class
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, candidates: Iterable[Any], item_limit: int = -1, *args, **kargs):
        """
        Class constructor

        :param Iterable[Any] candidates: iterable of candidate items to be added to the list
        :param int item_limit: limit of items that can be added, defaults to -1
        """
        super(ItemListEdit, self).__init__(*args, **kargs)

        assert (
            item_limit > 0 or item_limit == -1
        ), "Item limit must be greater than 0 or -1 (no limit)"

        self.item_limit = item_limit

        # Candidates
        self.candidates = candidates

        # Widgets
        self.item_list: QListWidget = None
        self.add_button: QPushButton = None
        self.remove_button: QPushButton = None

        self.create_component()

    # ----------------------------------------------------------------------
    # Method: create_component
    # Description: Creates the component
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self):
        # Item list
        self.item_list = QListWidget()
        self.item_list.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        # Reimplement sizeHint to set a minimun height of 80px
        # NOTE: Recomended in https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html
        self.item_list.sizeHint = lambda: QSize(0, 0)

        # Allow items movement using InternalMove and not Movement.Free because
        # Free duplicates the item when dragging and dropping.
        self.item_list.setMovement(QListWidget.Movement.Static)
        self.item_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Add and remove buttons
        self.add_button = QPushButton()
        add_button_icon = Icons().icon(ProteusIconType.App, "add_trace_icon")
        self.add_button.setIcon(add_button_icon)

        self.remove_button = QPushButton()
        self.remove_button.setEnabled(False)
        remove_button_icon = Icons().icon(ProteusIconType.App, "remove_trace_icon")
        self.remove_button.setIcon(remove_button_icon)

        # Create a layout for the buttons (vertically stacked)
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create a layout for the QTreeWidget and button layout (horizontally arranged)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.item_list)
        main_layout.addLayout(button_layout)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(main_layout)

        # Connect signals ----------

        # Buttons functionality
        # self.add_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        self.add_button.clicked.connect(self.add_item)

        # Update buttons
        self.item_list.itemClicked.connect(self.update_remove_button)
        self.item_list.itemClicked.connect(self.update_add_button)

        # Items changed
        self.itemsChanged.connect(self.update_add_button)
        self.itemsChanged.connect(self.update_remove_button)

    # ----------------------------------------------------------------------
    # Method: items
    # Description: Returns items data
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def items(self) -> List[Any]:
        """
        Returns items data

        :return: List of items data
        """
        items = []
        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            items.append(item.data(Qt.ItemDataRole.UserRole))
        return items

    # ----------------------------------------------------------------------
    # Method: setItems
    # Description: Set items data
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def setItems(self, items: Iterable[Any]):
        """
        Set items data

        :param items: Iterable items data
        """
        self.item_list.clear()
        for item in items:
            list_item = QListWidgetItem(self.item_list)
            self.list_item_setup(list_item, item)
            self.item_list.addItem(list_item)

    # ----------------------------------------------------------------------
    # Method: _list_item_setup
    # Description: Setup list item
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def list_item_setup(self, list_item: QListWidgetItem, item: Any):
        """
        Setup list item

        :param list_item: QListWidgetItem
        :param item: Any
        """
        list_item.setData(Qt.ItemDataRole.UserRole, item)
        list_item.setText(_(str(item)))

    # ======================================================================
    # Methods called by the signals
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method: remove_item
    # Description: Removes the selected item from the list widget without
    #              asking for confirmation.
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def remove_item(self):
        """
        Connected to the remove item button, it removes the selected item
        from the list widget without asking for confirmation.
        """
        # Get the current item
        current_item: QListWidgetItem = self.item_list.currentItem()

        # Remove the current item
        if current_item is not None:
            self.item_list.takeItem(self.item_list.row(current_item))

            self.itemsChanged.emit()

    # ----------------------------------------------------------------------
    # Method: update_remove_button
    # Description: Updates the remove button status.
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_remove_button(self):
        """
        Connected to the tree widget selection changed signal, it updates
        the remove button status.
        """
        if self.item_list.currentItem():
            self.remove_button.setEnabled(True)
        else:
            self.remove_button.setEnabled(False)

    # ----------------------------------------------------------------------
    # Method: update_add_button
    # Description: Updates the add button status.
    # Date: 31/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_add_button(self):
        """
        Updates the add button status. Called when an item is added, removed
        or the items are set for the first time.
        """
        items = self.items()
        if self.item_limit > 0 and len(items) >= self.item_limit:
            self.add_button.setEnabled(False)
        else:
            self.add_button.setEnabled(True)

    # ----------------------------------------------------------------------
    # Method: create_dialog
    # Date: 13/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_dialog(self, candidates: List[Any]) -> "ItemListEditDialog":
        """
        Creates the object picker dialog.
        """
        return ItemListEditDialog.create_dialog(candidates, self.list_item_setup)

    # ----------------------------------------------------------------------
    # Method: add_item
    # Description: Adds an item to the list widget.
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_item(self):
        """
        Adds an item to the list widget.
        """
        # Make the intersection between the candidates and the current items
        current_items = self.items()
        candidates = [item for item in self.candidates if item not in current_items]

        # Get the selected item
        dialog: ItemListEditDialog = self.create_dialog(candidates)

        select_item_data = dialog.selected_item_data

        # Add the item to the list
        if select_item_data is not None:
            list_item = QListWidgetItem(self.item_list)
            self.list_item_setup(list_item, select_item_data)
            self.item_list.addItem(list_item)

            self.itemsChanged.emit()


# --------------------------------------------------------------------------
# Class: ItemListEditDialog
# Description: item list edit dialog for the PROTEUS application
# Date: 06/11/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ItemListEditDialog(QDialog):
    """
    Provides an interface to select an item from a list of candidates.

    Setup method is provided from item list edit widget to customize the
    appearance of the items in the list. The dialog will return the data
    from Qt.ItemDataRole.UserRole of the selected items.
    """

    # ----------------------------------------------------------------------
    # Method: __init__
    # Description: Initializes the class
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self,
        candidates: Iterable[Any],
        setup_method: Callable[[QListWidgetItem, Any], None],
        *args,
        **kargs
    ):
        """
        Class constructor

        :param Iterable[Any] candidates: iterable of candidate items to be added to the list
        :param Callable[[QListWidgetItem, Any], None] setup_method: method to setup the items in the list
        """
        super(ItemListEditDialog, self).__init__(*args, **kargs)

        # Candidates
        self.candidates = candidates

        # Setup method
        self.setup_method = setup_method

        # Widgets
        self.error_label: QLabel = None
        self.item_list: QListWidget = None
        self.button_box: QDialogButtonBox = None
        self.name_filter_widget: QLineEdit = None

        # Layouts
        self.filters_layout: QHBoxLayout = None

        # Return variable
        self.selected_item_data: Any = None

        self.create_component()

    # ----------------------------------------------------------------------
    # Method: create_component
    # Description: Creates the component
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Creates the component
        """
        # -----------------------
        # Dialog general config
        # -----------------------

        # Set dialog title
        title: str = _("items_edit_dialog.title")
        self.setWindowTitle(title)

        # Set window icon
        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

        # -----------------------
        # Error label
        # -----------------------
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setHidden(True)
        self.error_label.setObjectName("error_label")

        # -----------------------
        # List widget setup
        # -----------------------

        # Create QListWidget to display selectable items
        self.item_list = QListWidget()
        self.item_list.setMovement(QListWidget.Movement.Static)
        self.item_list.setMinimumHeight(100)
        self.item_list.setMinimumWidth(400)

        # Add items to the list
        for item in self.candidates:
            list_item = QListWidgetItem(self.item_list)
            self.setup_method(list_item, item)
            self.item_list.addItem(list_item)

        # -----------------------
        # Name filter
        # -----------------------

        self.name_filter_widget = QLineEdit()
        self.name_filter_widget.setPlaceholderText(
            _("items_edit_dialog.name_filter_widget.placeholder_text")
        )

        # Connect textChanged signal
        self.name_filter_widget.textChanged.connect(self.update_item_list)

        # -----------------------
        # Buttonbox and layout
        # -----------------------

        # Create accept and reject buttons
        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            _("dialog.accept_button")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            _("dialog.reject_button")
        )

        # Filter layout
        self.filters_layout = QVBoxLayout()
        self.filters_layout.addWidget(self.name_filter_widget)

        # Create a layout for the QListWidget
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.filters_layout)
        main_layout.addWidget(self.item_list)
        main_layout.addWidget(self.error_label)
        main_layout.addWidget(self.button_box)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(main_layout)

        # -----------------------
        # Final setup
        # -----------------------

        # Connect signals
        self.item_list.currentItemChanged.connect(self.enable_accept_button)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.enable_accept_button()

        # If no objects are found, disable the accept button
        if len(self.candidates) == 0:
            self.item_list.setDisabled(True)

            self.error_label.setHidden(False)
            self.error_label.setText(_("items_edit_dialog.no_items_found"))

    # ======================================================================
    # Methods called by the signals
    # =================================================================

    # ----------------------------------------------------------------------
    # Method: update_item_list
    # Description: Updates the item list based on the name filter
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_item_list(self) -> None:
        """
        Updates the item list based on the name filter
        """
        filter_text = self.name_filter_widget.text().strip().lower()

        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            item_text = item.text().strip().lower()

            if filter_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)

        current_item = self.item_list.currentItem()
        if current_item:
            if current_item.isHidden():
                self.item_list.setCurrentItem(None)

    # ----------------------------------------------------------------------
    # Method: enable_accept_button
    # Description: Enables the accept button if an item is selected
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def enable_accept_button(self) -> None:
        """
        Enables the accept button if an item is selected
        """
        if self.item_list.currentItem():
            self.button_box.button(QDialogButtonBox.StandardButton.Save).setEnabled(
                True
            )
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Save).setEnabled(
                False
            )

    # ----------------------------------------------------------------------
    # Method: accept
    # Description: Accepts the dialog and sets the selected item data
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def accept(self) -> None:
        """
        Accepts the dialog and sets the selected item data
        """
        self.selected_item_data = self.item_list.currentItem().data(
            Qt.ItemDataRole.UserRole
        )
        super(ItemListEditDialog, self).accept()

    # ======================================================================
    # Static methods
    # =================================================================

    # ----------------------------------------------------------------------
    # Method: create_dialog
    # Description: Creates the dialog
    # Date: 06/11/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(
        candidates: Iterable[Any],
        setup_method: Callable[[QListWidgetItem, Any], None],
    ) -> Tuple[QDialog, Any]:
        """
        Creates the dialog

        :param Iterable[Any] candidates: iterable of candidate items to be added to the list
        :param Callable[[QListWidgetItem, Any], None] setup_method: method to setup the items in the list
        :return: created dialog
        """
        dialog = ItemListEditDialog(candidates, setup_method)
        dialog.exec()
        return dialog
