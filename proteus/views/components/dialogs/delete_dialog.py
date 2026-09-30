# ==========================================================================
# File: delete_dialog.py
# Description: PyQT6 delete dialog component for the PROTEUS application
# Date: 30/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict, Union

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QStyle,
    QLabel,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
)

# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusClassTag, ProteusID, PROTEUS_NAME
from proteus.model.object import Object
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.views.components.dialogs.base_dialogs import ProteusDialog
from proteus.controller.command_stack import Controller


# --------------------------------------------------------------------------
# Class: DeleteDialog
# Description: PyQT6 delete dialog component for the PROTEUS application
# Date: 30/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DeleteDialog(ProteusDialog):
    """
    Delete dialog component for the PROTEUS application. It provides a
    confirmation dialog to delete an object. It shows the object traces
    dependencies and ask the user to confirm the deletion.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 30/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self, element_id: ProteusID = None, is_document: bool = False, *args, **kwargs
    ) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Create properties to store the new document data.

        :param element_id: Element id to delete.
        :param is_document: True if the element is a document.
        """
        super(DeleteDialog, self).__init__(*args, **kwargs)

        self.element_id: ProteusID = element_id
        self.is_document: bool = is_document

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component
    # Date       : 30/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()

        # Set the dialog title
        self.setWindowTitle(_("delete_dialog.title"))

        # Set warning system icon
        warning_icon: QIcon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxWarning
        )
        self.setWindowIcon(warning_icon)

        # Get object name
        object: Object = self._controller.get_element(self.element_id)
        object_name: str = object.get_property(PROTEUS_NAME).value

        # Create confirmation message
        message: str = _("delete_dialog.message", object_name)
        message_label: QLabel = QLabel(message)
        layout.addWidget(message_label)
        layout.addStretch()

        # Show all the object traces dependencies, it is shown in a QTreeWidget.
        # Each object pointed by another object is shown as a parent item and
        # its dependencies are shown as children items.
        traces_dependencies: Dict[ProteusID, set] = (
            self._controller.get_traces_dependencies(self.element_id)
        )

        # Skipped if the object has no traces dependencies
        if traces_dependencies:

            # Explanation message
            message_traces: str = _("delete_dialog.traces_explanation")
            message_traces_label: QLabel = QLabel(message_traces)
            message_traces_label.setWordWrap(True)
            message_traces_label.setObjectName("message_traces_label")
            layout.addWidget(message_traces_label)

            # Create the tree widget and set expand policy
            tree: QTreeWidget = QTreeWidget()
            tree.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

            # Set header label
            header_message: str = _("delete_dialog.tree.header")
            tree.setHeaderLabel(header_message)
            # Disable selection
            tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)

            # Add object item
            for object_id in traces_dependencies.keys():
                # Create tree item
                item: QTreeWidgetItem = self.create_tree_item(object_id, tree)
                # Add children items
                for child_object_id in traces_dependencies[object_id]:
                    self.create_tree_item(child_object_id, item)

            layout.addWidget(tree)

        # Connect the button box signals to the slots
        self.accept_button.clicked.connect(self.save_button_clicked)

        self.set_content_layout(layout)

    def create_tree_item(
        self, object_id: ProteusID, parent: Union[QTreeWidget, QTreeWidgetItem]
    ) -> QTreeWidgetItem:
        """
        Create a tree item for the given object id. Sets the object name
        and icon.

        :param object_id: Object id
        :param parent: Parent tree item
        :return: Tree item
        """
        # Get object instance
        object: Object = self._controller.get_element(object_id)

        # Create tree item
        item: QTreeWidgetItem = QTreeWidgetItem(parent)

        # Set object name
        object_name: str = object.get_property(PROTEUS_NAME).value
        item.setText(0, object_name)

        # Set icon
        object_class: ProteusClassTag = object.classes[-1]
        icon = Icons().icon(ProteusIconType.Archetype, object_class)
        item.setIcon(0, icon)
        return item

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : save_button_clicked
    # Description: Save button clicked event handler
    # Date       : 30/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_button_clicked(self) -> None:
        """
        Manage the save button clicked event. It deletes the element and
        also the references to it and its children from other objects.
        """
        # Check if the object is a document
        if self.is_document:
            self._controller.delete_document(self.element_id)
        else:
            self._controller.delete_object(self.element_id)

        # Close the form window
        self.close()
        self.deleteLater()

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog
    # Description: Create a new document dialog and show it
    # Date       : 30/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(
        controller: Controller,
        element_id: ProteusID,
        is_document: bool = False,
    ) -> "DeleteDialog":
        """
        Create a delete dialog dialog and show it
        """
        dialog = DeleteDialog(
            element_id=element_id, is_document=is_document, controller=controller
        )
        dialog.exec()
        return dialog
