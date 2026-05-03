# ==========================================================================
# File: document_tree.py
# Description: PyQT6 document structure tree component for the PROTEUS
#              application
# Date: 25/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import Dict, List
import itertools
import string

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QDropEvent,
    QDragEnterEvent,
    QKeyEvent,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import (
    ProteusID,
    ProteusClassTag,
    PROTEUS_DOCUMENT,
    PROTEUS_NAME,
    PROTEUS_CODE,
)
from proteus.model.object import Object
from proteus.model.abstract_object import ProteusState
from proteus.model.properties.code_property import ProteusCode
from proteus.model.properties.property import Property
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.themes import Themes
from proteus.application.clipboard import Clipboard
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.views.components.dialogs.property_dialog import PropertyDialog
from proteus.views.components.dialogs.context_menu import ContextMenu
from proteus.application.events import (
    SelectObjectEvent,
    SaveProjectEvent,
    ModifyObjectEvent,
    AddObjectEvent,
    DeleteObjectEvent,
    SortChildrenEvent,
    ChangeObjectPositionEvent,
)


# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Global variables and constants
# --------------------------------------------------------------------------

# Map ProteusState to the key used in Themes().state_colors() so theme files
# can override every state's color from a single state_colors.json.
_STATE_TO_THEME_KEY = {
    ProteusState.FRESH: "fresh",
    ProteusState.DIRTY: "dirty",
    ProteusState.DEAD:  "dead",
    ProteusState.CLEAN: "clean",
}


def tree_item_brush(state: ProteusState) -> QBrush:
    """
    Return the QBrush used to paint a tree item for a given ProteusState.

    Reads the active theme's state_colors via the Themes singleton. Falls
    back to a sensible default if the theme has not been loaded yet (e.g.
    during early test setup).
    """
    theme_colors = Themes().state_colors()
    color: QColor = theme_colors.get(_STATE_TO_THEME_KEY[state])
    if color is None or not color.isValid():
        # Defensive default — shouldn't trigger in practice because
        # Themes.state_colors merges DEFAULT_STATE_COLORS on every call.
        color = QColor("#000000")
    return QBrush(color)


# --------------------------------------------------------------------------
# Class: DocumentTree
# Description: PyQT6 document structure tree component class for the PROTEUS
#              application
# Date: 25/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DocumentTree(QTreeWidget, ProteusComponent):
    """
    Document structure tree component for the PROTEUS application. It is used
    to manage the creation of the document structure tree and its actions.
    Display the document structure like a file system tree.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 27/05/2023
    # Version    : 0.2
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self,
        parent: QWidget,
        document_id: ProteusID,
        *args,
        **kwargs,
    ) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.

        Store the document id reference. Create the tree widget and the
        tree items dictionary to make easier the access to the tree items
        on update events using the element id.

        :param parent: Parent QWidget.
        :param document_id: The document id reference.
        """
        super(DocumentTree, self).__init__(parent, *args, **kwargs)

        # Set tree document id
        self.document_id: ProteusID = document_id

        # Tree items dictionary used to make easier the access to the tree
        # items on update events. Access by object id.
        self.tree_items: Dict[ProteusID, QTreeWidgetItem] = {}

        # Dead objects expanded state
        # This allows to restore the expanded state of dead and moved objects
        # TODO: Consider to store this as a class variable so objects can
        # be expanded(or not) when moving them across documents.
        self.dead_objects_expanded_state: Dict[ProteusID, bool] = {}

        # Create the component
        self.create_component()

        # Subscribe to events
        self.subscribe()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the document tree for the document referenced by
    #              the element id.
    # Date       : 25/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the document tree for the document referenced by the given
        document id. Set the tree properties, populate the tree and connect
        the tree signals.
        """
        # Set header
        self.header().setVisible(False)
        self.setIconSize(QSize(22, 22))

        # Set drag and drop properties
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)

        # Get document structure and top level items
        top_level_object: Object = self._controller.get_element(self.document_id)

        # Populate tree widget
        self._populate_tree(self, top_level_object)

        # Connect double click to object properties form
        self.itemDoubleClicked.connect(
            lambda item: PropertyDialog.create_dialog(
                element_id=item.data(1, Qt.ItemDataRole.UserRole),
                controller=self._controller,
            )
        )

        # Connect click to object selection
        self.itemPressed.connect(
            lambda item: self._state_manager.set_current_object(
                object_id=item.data(1, Qt.ItemDataRole.UserRole),
                document_id=self.document_id,
            )
        )

        # Set context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda position: ContextMenu.create_dialog(
                tree_widget=self, controller=self._controller, position=position
            )
        )

        # Expand all items and disable double click expand
        self.expandAll()
        self.setExpandsOnDoubleClick(False)

        self.update_indexes()

    # ----------------------------------------------------------------------
    # Method     : subscribe
    # Description: Subscribe to events.
    # Date       : 15/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def subscribe(self) -> None:
        """
        Subscribe the component to the events.

        DocumentTree component subscribes to the following events:
            - ADD OBJECT -> update_on_add_object
            - SAVE PROJECT -> update_on_save_project
            - MODIFY OBJECT -> update_on_modify_object
            - DELETE OBJECT -> update_on_delete_object
            - SELECT OBJECT -> update_on_select_object
            - SORT CHILDREN -> update_on_sort_children
            - CHANGE OBJECT POSITION -> update_on_change_object_position
        """
        AddObjectEvent().connect(self.update_on_add_object)
        SaveProjectEvent().connect(self.update_on_save_project)
        ModifyObjectEvent().connect(self.update_on_modify_object)
        DeleteObjectEvent().connect(self.update_on_delete_object)
        SelectObjectEvent().connect(self.update_on_select_object)
        SortChildrenEvent().connect(self.update_on_sort_children)
        ChangeObjectPositionEvent().connect(self.update_on_change_object_position)

    # ----------------------------------------------------------------------
    # Method     : _populate_tree
    # Description: Populate document tree given the document structure
    # Date       : 04/06/2023
    # Version    : 0.2
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _populate_tree(
        self, parent_item: QTreeWidgetItem, object: Object, position=None
    ):
        """
        Populate the document tree given an object. This method is recursive.
        Iterate over the object children and populate the tree with them.

        :param parent_item: The parent item of the object
        :param object: The object to populate the tree
        :param position: The position to insert the item in the parent item, if None
                            the item is appended at the end.
        """
        # If object is DEAD do not add it to the tree
        if object.state == ProteusState.DEAD:
            return

        # Create the new item, if position is not None insert the item in
        # the given position
        if position is not None:
            new_item = QTreeWidgetItem()
            parent_item.insertChild(position, new_item)
        else:
            new_item = QTreeWidgetItem(parent_item)

        # Set the item data to store the object id
        new_item.setData(1, Qt.ItemDataRole.UserRole, object.id)

        # Setup the new item with object information
        self._tree_item_setup(new_item)

        # Add the new item to the tree items dictionary
        self.tree_items[object.id] = new_item

        # Check if the object has children
        for child in object.children:
            self._populate_tree(new_item, child)

    # ----------------------------------------------------------------------
    # Method     : _tree_item_setup
    # Description: Setup the tree item for the given object.
    # Date       : 01/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _tree_item_setup(self, tree_item: QTreeWidgetItem) -> None:
        """
        Given an object, update the tree item properties to match the object
        properties and state.

        :param tree_item: The tree item to update
        :param object: The object to match
        """
        # Get the object from the item data
        object_id: ProteusID = tree_item.data(1, Qt.ItemDataRole.UserRole)
        object: Object = self._controller.get_element(object_id)

        # Set the background color based on the object ProteusState
        tree_item.setForeground(0, tree_item_brush(object.state))

        # Set the icon based on the object last class
        object_class: ProteusClassTag = object.classes[-1]
        icon = Icons().icon(ProteusIconType.Archetype, object_class)
        tree_item.setIcon(0, icon)

        # Create item string from object properties --------------------------------
        name_str = ""
        code_str = ""

        # Check for PROTEUS_CODE property
        if object.get_property(PROTEUS_CODE) is not None:
            code: ProteusCode = object.get_property(PROTEUS_CODE).value

            # If not instance of ProteusCode, cast to string and log warning
            if isinstance(code, ProteusCode):
                code_str = f"[{code.to_string()}]"
            else:
                log.warning(
                    f"PROTEUS_CODE property of object {object.id} is not instance of ProteusCode, casting to string."
                )
                code_str = f"[{str(code)}]"

        # Check for PROTEUS_NAME property
        name_property = object.get_property(PROTEUS_NAME)

        assert isinstance(
            name_property, Property
        ), f"Every object must have a PROTEUS_NAME property. Check object {object.id} properties, current return type is {type(name_property)}"

        name_str = str(name_property.value)

        # Numbered prefix ----------------------------------------------
        numbered_str = ""

        # Check if the object is numbered and has a parent (not a document)
        if isinstance(object.parent, Object) and tree_item.parent() is not None:
            if object.parent.numbered:
                # Get the index of the item in the parent
                index = tree_item.parent().indexOfChild(tree_item) + 1
                # Numbered string
                numbered_str = f"{index}. "

        # Build the name string
        item_string = f"{numbered_str}{code_str} {name_str}".strip()
        tree_item.setText(0, item_string)

        # Set the expanded state of the item if it is stored in the dead objects
        # expanded state dictionary
        if object.id in self.dead_objects_expanded_state:
            tree_item.setExpanded(self.dead_objects_expanded_state[object.id])
            self.dead_objects_expanded_state.pop(object.id)

    # ----------------------------------------------------------------------
    # Method     : _delete_tree_item
    # Description: Delete the tree item widget and its children recursively.
    # Date       : 20/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _delete_tree_item(self, item: QTreeWidgetItem) -> None:
        """
        Helper method to delete item widget and its children recursively.
        """
        # Get the children widgets
        children_widgets: List[QTreeWidgetItem] = [
            item.child(i) for i in range(item.childCount())
        ]

        # Iterate over the children widgets
        for child_widget in children_widgets:
            self._delete_tree_item(child_widget)

        # Item id
        item_id: ProteusID = item.data(1, Qt.ItemDataRole.UserRole)

        # Save the expanded state of the item
        self.dead_objects_expanded_state[item_id] = item.isExpanded()

        # Remove the item from its parent
        item.parent().removeChild(item)

        # Remove the item from the tree items dictionary
        self.tree_items.pop(item_id)

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_on_modify_object
    # Description: Update the document tree when an object is modified.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_modify_object(self, object_id: ProteusID) -> None:
        """
        Update the document tree when an object is modified. Look for the
        object in the tree items dictionary and update the tree item properties.

        Triggered by: ModifyObjectEvent

        :param object_id: The object id to update
        """
        # Check the object id is not None
        assert (
            object_id is not None or object_id != ""
        ), "Object id is None on MODIFY OBJECT event"

        # Check if the element id is in the tree items dictionary
        if object_id not in self.tree_items:
            return

        # Get the tree item
        tree_item: QTreeWidgetItem = self.tree_items[object_id]

        # Get the object
        object: Object = self._controller.get_element(object_id)

        assert isinstance(
            object, Object
        ), "Object is not instance of Object in MODIFY OBJECT event"

        # Update the tree item with the object information
        self._tree_item_setup(tree_item)

        self.update_indexes()

    # ----------------------------------------------------------------------
    # Method     : update_on_save_project
    # Description: Update the document tree when a project is saved.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_save_project(self) -> None:
        """
        Update the document tree when a project is saved. Iterate over the
        tree items and set the color to black (no changes).

        Triggered by: SaveProjectEvent
        """
        items = self.tree_items.values()
        for tree_item in items:
            tree_item.setForeground(0, tree_item_brush(ProteusState.CLEAN))

    # ----------------------------------------------------------------------
    # Method     : update_on_add_object
    # Description: Update the document tree when an object is added.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_add_object(self, object_id: ProteusID) -> None:
        """
        Update the document tree when an object is added. Look for the
        parent item in the tree items dictionary and add the new item to
        the parent item including the new object children. Update the parent
        item color based on the parent object ProteusState.

        Triggered by: AddObjectEvent

        :param object_id: The object id to add to the tree
        """
        # Check the object id is not None
        assert (
            object_id is not None or object_id != ""
        ), "Object id is None on ADD OBJECT event"

        # Get the new object
        new_object: Object = self._controller.get_element(object_id)

        # Check the object is instance of Object
        assert isinstance(
            new_object, Object
        ), "Object is not instance of Object on ADD OBJECT event"

        # Check if the parent item is in the tree items dictionary
        if new_object.parent.id not in self.tree_items:
            return

        # Get the parent item
        parent_item: QTreeWidgetItem = self.tree_items[new_object.parent.id]
        parent_item.setExpanded(True)

        # Update the parent item color
        # NOTE: Parent will always be an Object. Project cannot be selected
        #       as parent to trigger ADD_OBJECT event. When adding an object
        #       with Project as parent ADD_DOCUMENT event is triggered.
        parent: Object = self._controller.get_element(new_object.parent.id)
        parent_item.setForeground(0, tree_item_brush(parent.state))

        # Calculate item position relative to its siblings omits DEAD objects
        siblings: List[Object] = [
            s
            for s in new_object.parent.get_descendants()
            if s.state != ProteusState.DEAD
        ]
        position: int = siblings.index(new_object)

        # Create the new item
        self._populate_tree(parent_item, new_object, position=position)

        # Scroll to the new item (parent remains selected)
        self.scrollToItem(
            self.tree_items[new_object.id], QTreeWidget.ScrollHint.EnsureVisible
        )

        # If parent numbered is True, update every sibling number
        if new_object.parent.numbered:
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                self._tree_item_setup(child)

        self.update_indexes()

    # ----------------------------------------------------------------------
    # Method     : update_on_delete_object
    # Description: Update the document tree when an object is deleted.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_delete_object(self, object_id: ProteusID) -> None:
        """
        Update the document tree when an object is deleted. Look for the
        object in the tree items dictionary and remove the item from its
        parent item and tree items dictionary. Update the parent item color
        based on the parent object ProteusState.

        Triggered by: DeleteObjectEvent

        :param object_id: The object id to delete from the tree
        """

        # Check the element id is not None
        assert (
            object_id is not None or object_id != ""
        ), "Object id is None on DELETE OBJECT event"

        # Check if the element id is in the tree items dictionary
        if object_id not in self.tree_items:
            return

        # Get the tree item
        tree_item: QTreeWidgetItem = self.tree_items[object_id]

        # Get parent object to update the color
        # NOTE: Parent will always be an Object. Project cannot be selected
        #       as parent to trigger DELETE_OBJECT event. When deleting object
        #       with Project parent DELETE_DOCUMENT event is triggered.
        parent_id: ProteusID = tree_item.parent().data(1, Qt.ItemDataRole.UserRole)
        parent_object: Object = self._controller.get_element(parent_id)
        tree_item.parent().setForeground(0, tree_item_brush(parent_object.state))

        # Remove the item from the tree including its children
        self._delete_tree_item(tree_item)

        # Set current item to None
        self._state_manager.deselect_object(object_id)

        # If parent numbered is True, update every sibling number
        if parent_object.numbered:
            for i in range(self.tree_items[parent_id].childCount()):
                child = self.tree_items[parent_id].child(i)
                self._tree_item_setup(child)

        self.update_indexes()

    # ----------------------------------------------------------------------
    # Method     : update_on_select_object
    # Description: Update the document tree when an object is selected.
    # Date       : 20/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_select_object(
        self,
        selected_object_id: ProteusID,
        document_id: ProteusID,
        navigate: bool,
        scroll_behavior: QTreeWidget.ScrollHint,
    ) -> None:
        """
        Update the document tree when an object is selected. Look for the
        object in the tree items dictionary and select the item.

        Triggered by: SelectObjectEvent

        :param selected_object_id: The object id to select
        :param document_id: The document id reference
        """
        # Skip if the document id is different from the tree document id
        if document_id != self.document_id:
            return

        # Check if the element id is in the tree items dictionary
        if selected_object_id not in self.tree_items:
            self.setCurrentItem(None)
        else:
            # Get the tree item
            tree_item: QTreeWidgetItem = self.tree_items[selected_object_id]

            # Deselect all items, this forces to select the item again
            # in case it is already selected (useful for expanding the parents)
            self.setCurrentItem(None)

            # Select the item
            self.setCurrentItem(tree_item)
            self.scrollToItem(tree_item, scroll_behavior)

    # ----------------------------------------------------------------------
    # Method     : update_on_sort_children
    # Description: Update the document tree when the children of an object
    #              are sorted.
    # Date       : 20/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_sort_children(self, parent_id: ProteusID) -> None:
        """
        Update the document tree when the children of an object/document are
        sorted. Look for the parent object in the tree items dictionary and
        sort the children items.

        Triggered by: SortChildrenEvent

        :param parent_id: The parent object id to sort the children
        """
        # Check the parent id is not None
        assert (
            parent_id is not None or parent_id != ""
        ), "Parent id is None on SORT CHILDREN event"

        # Check if the parent id is in the tree items dictionary
        if parent_id not in self.tree_items:
            return

        # Get the parent item
        parent_item: QTreeWidgetItem = self.tree_items[parent_id]

        # Get the parent object
        parent_object: Object = self._controller.get_element(parent_id)

        # Check the parent object is instance of Object
        assert isinstance(
            parent_object, Object
        ), "Parent object is not instance of Object on SORT CHILDREN event"

        # Get the children objects
        children_objects: List[Object] = parent_object.get_descendants()

        # Get the children tree items
        children_items: List[QTreeWidgetItem] = [
            self.tree_items[child.id]
            for child in children_objects
            if child.state != ProteusState.DEAD
        ]

        # NOTE: Helper functions to get and set the expanded state of the object
        # this is necessary to keep the expanded state of the object and its children
        # when sorting the children items.
        def _get_expanded_state(item: QTreeWidgetItem) -> Dict[ProteusID, bool]:
            expanded_state_dict: Dict[ProteusID, bool] = {}
            n_children = item.childCount()
            for i in range(n_children):
                child_item = item.child(i)
                expanded_state_dict.update(_get_expanded_state(child_item))
                expanded_state_dict[child_item.data(1, Qt.ItemDataRole.UserRole)] = (
                    child_item.isExpanded()
                )
            return expanded_state_dict

        def _set_expanded_state(
            item: QTreeWidgetItem, expanded_state_dict: Dict[ProteusID, bool]
        ) -> None:
            n_children = item.childCount()
            for i in range(n_children):
                child_item = item.child(i)
                _set_expanded_state(child_item, expanded_state_dict)
                child_item.setExpanded(
                    expanded_state_dict[child_item.data(1, Qt.ItemDataRole.UserRole)]
                )

        # Expanded state of the object and its children
        expanded_state_dict: Dict[ProteusID, bool] = _get_expanded_state(parent_item)

        # Sort the children items
        for i, child_item in enumerate(children_items):
            parent_item.removeChild(child_item)
            parent_item.insertChild(i, child_item)

        # Set the expanded state of the object and its children
        _set_expanded_state(parent_item, expanded_state_dict)

        # If parent numbered is True, update every sibling number
        if parent_object.numbered:
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                self._tree_item_setup(child)

        self.update_indexes()

    # ----------------------------------------------------------------------
    # Method     : update_on_change_object_position
    # Description: Update the document tree when an object is moved.
    # Date       : 20/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_change_object_position(self, object_id: ProteusID) -> None:
        """
        Update the document tree when an object is moved. Look for the
        object in the tree items dictionary and update the tree item
        position.

        Triggered by: ChangeObjectPositionEvent

        :param object_id: The object id to move
        """
        # Check the object id is not None
        assert (
            object_id is not None or object_id != ""
        ), "Object id is None on CHANGE OBJECT POSITION event"

        object: Object = self._controller.get_element(object_id)

        # Item removal from tree ----------------
        if object_id in self.tree_items.keys():

            # Update the old parent item color
            # NOTE: Parent will always be an Object. Project cannot be selected
            #       as parent to trigger CHANGE_OBJECT_POSITION event.
            parent_item: QTreeWidgetItem = self.tree_items[object_id].parent()
            parent: Object = self._controller.get_element(
                parent_item.data(1, Qt.ItemDataRole.UserRole)
            )
            parent_item.setForeground(0, tree_item_brush(parent.state))

            # Remove the item from the tree
            self._delete_tree_item(self.tree_items[object_id])
            self._state_manager.deselect_object(object_id)

            # If parent numbered is True, update every sibling number
            if parent.numbered:
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    self._tree_item_setup(child)

        # Item insertion in tree ----------------
        if object.parent.id in self.tree_items.keys():
            parent_item: QTreeWidgetItem = self.tree_items[object.parent.id]

            # Update the parent item color
            # NOTE: Parent will always be an Object. Project cannot be selected
            #       as parent to trigger CHANGE_OBJECT_POSITION event.
            parent: Object = self._controller.get_element(object.parent.id)
            parent_item.setForeground(0, tree_item_brush(parent.state))

            # Calculate item position relative to its siblings omits DEAD objects
            siblings: List[Object] = [
                s
                for s in object.parent.get_descendants()
                if s.state != ProteusState.DEAD
            ]
            position: int = siblings.index(object)

            self._populate_tree(parent_item, object, position)
            self._state_manager.set_current_object(object_id, self.document_id)

            # If parent numbered is True, update every sibling number
            if parent.numbered:
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    self._tree_item_setup(child)

        self.update_indexes()

    # ======================================================================
    # Component slots methods (connected to the component signals)
    # ======================================================================

    # ======================================================================
    # Component overriden methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : dropEvent
    # Description: Manage the drop event. Move the dropped object to the
    #              target position.
    # Date       : 14/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def dropEvent(self, event: QDropEvent):
        # Get the object that performs the drop
        # NOTE: When drop is performed across different documents, source
        # reference is the source tree widget and this drop event is called'
        # from the target tree widget. This is necessary to get the dropped
        # item.
        source: QTreeWidget = event.source()

        # Prevent drop non qt objects
        if source is None:
            return

        # Get dropped element_id
        dropped_item = source.currentItem()
        dropped_element_id: ProteusID = dropped_item.data(1, Qt.ItemDataRole.UserRole)

        # Drop position
        point: QPoint = event.position().toPoint()

        # Get target element_id
        target_item = self.itemAt(point)
        try:
            target_element_id: ProteusID = target_item.data(1, Qt.ItemDataRole.UserRole)
        except AttributeError:
            log.warning(f"Target item not found at position {point}.")
            return

        # Check if dropped item and target item are not None
        if dropped_item and target_item:
            # Determine the drop behavior based on the drop position.
            # If drop position is in the middle of the target item (50% height
            # centered at the target item), then the dropped item will
            # be added as a child of the target item. Otherwise, the dropped
            # item will be added as a sibling of the target item depending on
            # the drop position (above or below the target item).
            target_rect = self.visualItemRect(target_item)
            rect_center = target_rect.center()
            rect_height = target_rect.height()

            # Get the index of the target item
            target_index: int = self.indexFromItem(target_item).row()

            # Get the parent id
            parent_id: ProteusID = None
            try:
                parent_id: ProteusID = target_item.parent().data(
                    1, Qt.ItemDataRole.UserRole
                )
            except AttributeError:
                log.debug(
                    f"Failed to get the parent id of the target item '{target_element_id}'. The target item is a root item (PROTEUS document)"
                )

            try:
                # Check the dropped item is different from the target item
                assert (
                    dropped_element_id != target_element_id
                ), f"Cannot drop element {dropped_element_id} on itself."

                # If in the 25% of the bottom of the target item, then add the
                # dropped item as a sibling above the target item
                if (
                    event.position().y() > rect_center.y() + rect_height / 4
                    and parent_id
                ):
                    log.info(
                        f"Tree element with id {dropped_element_id} dropped below {target_index} insert in {target_index + 1} parent {parent_id}."
                    )
                    self._controller.change_object_position(
                        dropped_element_id, parent_id, target_index + 1
                    )

                # If in the 25% of the top of the target item, then add the
                # dropped item as a sibling below the target item
                elif (
                    event.position().y() < rect_center.y() - rect_height / 4
                    and parent_id
                ):
                    log.info(
                        f"Tree element with id {dropped_element_id} dropped above {target_index} insert in {target_index} parent {parent_id}."
                    )
                    self._controller.change_object_position(
                        dropped_element_id, parent_id, target_index
                    )

                # If in the middle of the target item, then add the dropped item
                # as a child of the target item. Position as None means that the
                # dropped item will be added as the last child of the target item.
                else:
                    log.info(
                        f"Tree element with id {dropped_element_id} dropped inside {target_element_id} inserted at the end of the children list."
                    )
                    self._controller.change_object_position(
                        dropped_element_id, target_element_id
                    )
            # Catch exception in case the operation is forbidden
            except AssertionError as e:
                log.warning(f"{e}")

                MessageBox.warning(
                    _("document_tree.drop_action.message_box.error.title"),
                    _("document_tree.drop_action.message_box.error.text"),
                )

    # ----------------------------------------------------------------------
    # Method     : dragEnterEvent
    # Description: Manage the drag enter event. Check if the dragged
    #              QTreeWidgetItem is a :Proteus-document class, if so do
    #              not allow the drag event.
    # Date       : 02/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Check if the dragged QTreeWidgetItem is a :Proteus-document class,
        if so do not allow the drag event.
        """
        super().dragEnterEvent(event)
        # Get the object that performs the drag
        source: QTreeWidget = event.source()

        # Prevent drag non qt objects
        if source is None:
            return

        source_item: QTreeWidgetItem = source.currentItem()
        source_item_id: ProteusID = source_item.data(1, Qt.ItemDataRole.UserRole)

        # Get the object
        object: Object = self._controller.get_element(source_item_id)

        # Check PROTEUS class
        if PROTEUS_DOCUMENT in object.classes:
            event.ignore()
            return
        else:
            event.accept()
            return

    # ----------------------------------------------------------------------
    # Method     : keyPressEvent
    # Description: Manage the key press event for the tree widget.
    # Date       : 15/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Manage the key press event for the tree widget.

        Implemented actions:
            - Copy: Copy the selected item id to the clipboard (omit documents)
            - Paste: Paste the copied item id as a child of the selected item
        """

        # ------------------------------------------------------------------
        # Clipboard events
        # ------------------------------------------------------------------
        if event.matches(QKeySequence.StandardKey.Cut):
            Clipboard().cut()
            return event.accept()

        if event.matches(QKeySequence.StandardKey.Copy):
            Clipboard().copy()
            return event.accept()

        if event.matches(QKeySequence.StandardKey.Paste):
            Clipboard().paste()
            return event.accept()

        # ------------------------------------------------------------------
        # Enter key event
        # ------------------------------------------------------------------
        # Open the properties dialog when the enter key is pressed
        if event.key() == Qt.Key.Key_Return:
            selected_item = self.currentItem()
            if selected_item:
                object_id = selected_item.data(1, Qt.ItemDataRole.UserRole)
                PropertyDialog.create_dialog(
                    element_id=object_id, controller=self._controller
                )
            return event.accept()

        # ------------------------------------------------------------------
        # Default event (Handle current item changes)
        # ------------------------------------------------------------------
        # NOTE: currentItemChanged signal is not triggered when the current item
        # changes using the keyboard.

        previous_item = self.currentItem()
        super().keyPressEvent(event)
        current_item = self.currentItem()

        if previous_item != current_item and current_item:
            object_id = current_item.data(1, Qt.ItemDataRole.UserRole)
            self._state_manager.set_current_object(object_id, self.document_id)

        return event.accept()

    # ======================================================================
    # Index handling methods
    # TODO: Implement this as an abstract feature that can be enabled for
    #       specific classes
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_indexes
    # Description: Update the section indexes for all the sections in the
    #              document.
    # Date       : 12/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_indexes(self) -> None:
        """
        Update the section indexes for all the sections in the document.
        """
        # Get the top level object
        top_level_object: Object = self._controller.get_element(self.document_id)

        # Calculate the section indexes
        self._calculate_section_indexes(top_level_object)

        # Calculate the appendix indexes
        self._calculate_appendix_indexes(top_level_object)

    # ----------------------------------------------------------------------
    # Method     : _calculate_section_indexes
    # Description: Calculate the section indexes for all the sections in the
    #              document.
    # Date       : 12/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _calculate_section_indexes(
        self, object: Object, acumulated_index: str = ""
    ) -> None:
        """
        Calculate the section indexes for all the sections in the document.
        Uses numeric indexes for sections.

        Uses recursive calls to calculate the section indexes for all the
        nested sections.

        :param object: The object to calculate the section indexes
        :param acumulated_index: The acumulated index for the object
        """
        numeric_index = 1

        for child in object.get_descendants():

            # Skip if object is DEAD or not a section
            if (
                child.state == ProteusState.DEAD
                or child.classes[-1] != "section"
                or child.id not in self.tree_items
            ):
                continue

            # Set the section index
            child_index = ""
            if acumulated_index == "":
                child_index = f"{str(numeric_index)}"
            else:
                child_index = f"{acumulated_index}.{str(numeric_index)}"
            numeric_index += 1

            # Set the section index
            tree_element = self.tree_items[child.id]
            section_name = child.get_property(PROTEUS_NAME).value
            tree_element.setText(0, f"{child_index} {section_name}")

            # Calculate the section index for the children
            self._calculate_section_indexes(child, acumulated_index=child_index)

    # ----------------------------------------------------------------------
    # Method     : _calculate_appendix_indexes
    # Description: Calculate the appendix indexes for all the appendices in
    #              the document.
    # Date       : 29/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _calculate_appendix_indexes(self, object: Object) -> None:
        """
        Calculate the appendix indexes for all the appendices in the document.
        Uses alphabetic indexes for appendices.

        Recursive calls are only necessary for the appendices children if there
        are sections inside the appendices.

        :param object: The object to calculate the appendix indexes
        """
        alpha_index = alpha_sequence()

        for child in object.get_descendants():

            # Skip if object is DEAD or not an appendix
            if (
                child.state == ProteusState.DEAD
                or child.classes[-1] != "appendix"
                or child.id not in self.tree_items
            ):
                continue

            # Set the appendix index
            child_index = next(alpha_index)

            # Set the appendix index
            tree_element = self.tree_items[child.id]
            appendix_name = child.get_property(PROTEUS_NAME).value
            tree_element.setText(0, f"{child_index} {appendix_name}")

            # Calculate the section index for the children
            self._calculate_section_indexes(child, acumulated_index=child_index)


# ======================================================================
# Helper functions
# ======================================================================


# ----------------------------------------------------------------------
# Function   : alpha_sequence
# Description: Generate an infinite sequence of uppercase alphabetic
#              characters.
# Date       : 12/07/2024
# Version    : 0.1
# Author     : José María Delgado Sánchez
# ----------------------------------------------------------------------
def alpha_sequence():
    """
    Generate an infinite sequence of uppercase alphabetic characters.
    """
    for length in itertools.count(1):
        for s in itertools.product(string.ascii_uppercase, repeat=length):
            yield "".join(s)
