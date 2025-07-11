# ==========================================================================
# File: context_menu.py
# Description: PyQT6 context menu component.
# Date: 18/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List, Dict, Tuple

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_NAME, PROTEUS_DOCUMENT
from proteus.model.object import Object
from proteus.model.project import Project
from proteus.controller.command_stack import Controller
from proteus.application.configuration.config import Config
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.clipboard import Clipboard
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.dialogs.property_dialog import PropertyDialog
from proteus.views.components.dialogs.delete_dialog import DeleteDialog
from proteus.views.components.developer.model_editor import RawObjectEditor
from proteus.views.components.developer.create_object_archetype import (
    CreateObjectArchetypeDialog,
)
from proteus.views.components.developer.create_document_archetype import (
    CreateDocumentArchetypeDialog,
)


# --------------------------------------------------------------------------
# Class: ContextMenu
# Description: Class for the PROTEUS application context menu.
# Date: 09/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ContextMenu(QMenu, ProteusComponent):
    """
    Class for the PROTEUS application objects context menu. The menu shows
    the available actions for the selected object. It also shows a submenu
    with the available archetypes to clone in the selected object if needed.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, tree_widget: QTreeWidget, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Store the tree widget and initialize all the action
        buttons.

        :param tree_widget: QTreeWidget instance.
        """
        super(ContextMenu, self).__init__(*args, **kwargs)

        assert isinstance(
            tree_widget, QTreeWidget
        ), f"tree_widget must be a QTreeWidget instance, not {type(tree_widget)}"

        # Dependencies
        self.tree_widget = tree_widget

        # Context menu owner (element object)
        self.element: Object = None

        # Action buttons (stored in order to make testing easier)
        self.action_edit_object: QAction = None
        self.action_delete_object: QAction = None
        self.action_clone_object: QAction = None
        self.action_move_up_object: QAction = None
        self.action_move_down_object: QAction = None
        self.action_copy_object: QAction = None
        self.action_paste_object: QAction = None

        self.submenu_children_sort: QMenu = None
        self.action_children_sort: QAction = None
        self.action_children_sort_reverse: QAction = None

        # Developer actions
        self.action_edit_model: QAction = None
        self.action_store_object_as_archetype: QAction = None
        self.action_store_document_as_archetype: QAction = None

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component.
        """
        # Get the selected item
        selected_item: QTreeWidgetItem = self.tree_widget.currentItem()

        # Check if the selected item is not None
        if selected_item is None:
            return

        # Get the selected item id
        selected_item_id: ProteusID = selected_item.data(1, Qt.ItemDataRole.UserRole)

        # NOTE: Elements stored in the tree items dictionary are always
        #       Objects.
        self.element: Object = self._controller.get_element(selected_item_id)

        # Actions
        self.action_edit_object = self._create_edit_action()
        self.action_delete_object = self._create_delete_action()
        self.action_clone_object = self._create_clone_action()
        self.action_copy_object = self._create_copy_action()
        self.action_cut_object = self._create_cut_action()
        self.action_paste_object = self._create_paste_action()
        self.action_move_up_object, self.action_move_down_object = (
            self._create_move_up_down_actions()
        )
        self.action_edit_model = self._create_edit_model_action()
        self.action_store_object_as_archetype = self._create_store_object_as_archetype_action()
        self.action_store_document_as_archetype = self._create_store_document_as_archetype_action()

        # Sort submenu
        self.submenu_children_sort = self._create_sort_submenu()

        # Add the actions to the context menu ------------------------------
        self.addAction(self.action_edit_object)
        self.addAction(self.action_delete_object)
        self.addAction(self.action_clone_object)

        self.addSeparator()

        # Developer actions
        if Config().app_settings.developer_features:
            self.addAction(self.action_edit_model)
            self.addAction(self.action_store_object_as_archetype)
            self.addAction(self.action_store_document_as_archetype)

            self.addSeparator()

        # Insert the copy and paste actions
        self.addAction(self.action_cut_object)
        self.addAction(self.action_copy_object)
        self.addAction(self.action_paste_object)

        self.addSeparator()

        # Insert the accepted archetypes clone menus
        accepted_archetypes: Dict[str, List[Object]] = (
            self._controller.get_accepted_object_archetypes(selected_item_id)
        )
        for archetype_class in accepted_archetypes.keys():
            # Create the archetype menu
            archetype_menu: AvailableArchetypesMenu = AvailableArchetypesMenu(
                parent_id=selected_item_id,
                class_name=archetype_class,
                archetype_list=accepted_archetypes[archetype_class],
                parent=self,
            )
            # Add the archetype menu to the context menu
            self.addMenu(archetype_menu)

        self.addSeparator()

        self.addMenu(self.submenu_children_sort)
        self.addAction(self.action_move_up_object)
        self.addAction(self.action_move_down_object)

    # ---------------------------------------------------------------------
    # Method     : _create_edit_action
    # Description: Create the edit action.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_edit_action(self) -> QAction:
        """
        Create the edit action.
        """
        action: QAction = QAction(_("document_tree.menu.action.edit"), self)
        action.triggered.connect(
            lambda: PropertyDialog.create_dialog(
                element_id=self.element.id, controller=self._controller
            )
        )
        edit_icon = Icons().icon(ProteusIconType.App, "context-menu-edit")
        action.setIcon(edit_icon)

        # Visibility and state restrictions (not needed for this action)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_delete_action
    # Description: Create the delete action.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_delete_action(self) -> QAction:
        """
        Create the delete action.
        """
        is_document: bool = isinstance(self.element.parent, Project)

        action: QAction = QAction(_("document_tree.menu.action.delete"), self)
        action.triggered.connect(
            lambda: DeleteDialog.create_dialog(
                element_id=self.element.id,
                controller=self._controller,
                is_document=is_document,
            )
        )
        delete_icon = Icons().icon(ProteusIconType.App, "context-menu-delete")
        action.setIcon(delete_icon)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_clone_action
    # Description: Create the clone action.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_clone_action(self) -> QAction:
        """
        Create the clone action.
        """
        action: QAction = QAction(_("document_tree.menu.action.clone"), self)
        action.triggered.connect(lambda: self._controller.clone_object(self.element.id))
        clone_icon = Icons().icon(ProteusIconType.App, "context-menu-clone")
        action.setIcon(clone_icon)

        # Disable the clone action if the element is a document
        if PROTEUS_DOCUMENT in self.element.classes:
            action.setEnabled(False)
            action.setVisible(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_copy_action
    # Description: Create the copy action.
    # Date       : 15/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_copy_action(self) -> QAction:
        """
        Create the copy action.
        """
        action: QAction = QAction(_("document_tree.menu.action.copy"), self)
        action.triggered.connect(Clipboard().copy)
        copy_icon = Icons().icon(ProteusIconType.App, "context-menu-copy")
        action.setIcon(copy_icon)

        # Disable the action if the element is a document
        if not Clipboard().can_cut_and_copy():
            action.setEnabled(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_cut_action
    # Description: Create the cut action.
    # Date       : 30/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_cut_action(self) -> QAction:
        """
        Create the cut action.
        """
        action: QAction = QAction(_("document_tree.menu.action.cut"), self)
        action.triggered.connect(Clipboard().cut)
        cut_icon = Icons().icon(ProteusIconType.App, "context-menu-cut")
        action.setIcon(cut_icon)

        # Disable the action if the element is a document
        if not Clipboard().can_cut_and_copy():
            action.setEnabled(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_paste_action
    # Description: Create the paste action.
    # Date       : 15/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_paste_action(self) -> QAction:
        """
        Create the paste action.
        """
        action: QAction = QAction(_("document_tree.menu.action.paste"), self)

        # Connect the action to the controller method
        action.triggered.connect(Clipboard().paste)
        paste_icon = Icons().icon(ProteusIconType.App, "context-menu-paste")
        action.setIcon(paste_icon)

        # Check if the object can be pasted
        if not Clipboard().can_paste():
            action.setEnabled(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_move_up_down_actions
    # Description: Create the move up and move down actions.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_move_up_down_actions(self) -> Tuple[QAction, QAction]:
        """
        Create the move up and move down actions.
        """
        # Position related information
        selected_item: QTreeWidgetItem = self.tree_widget.currentItem()
        position_index: int = self.tree_widget.indexFromItem(selected_item).row()

        # Create move up action ---------------------------------------------
        action_move_up: QAction = QAction(_("document_tree.menu.action.move_up"), self)

        action_move_up.triggered.connect(
            lambda: self._controller.change_object_position(
                self.element.id, self.element.parent.id, position_index - 1
            )
        )
        move_up_icon = Icons().icon(ProteusIconType.App, "context-menu-up")
        action_move_up.setIcon(move_up_icon)

        # Create move down action -------------------------------------------
        action_move_down: QAction = QAction(
            _("document_tree.menu.action.move_down"), self
        )
        action_move_down.triggered.connect(
            lambda: self._controller.change_object_position(
                self.element.id, self.element.parent.id, position_index + 2
            )
        )
        move_down_icon = Icons().icon(ProteusIconType.App, "context-menu-down")
        action_move_down.setIcon(move_down_icon)

        # Disable the move up action if the element is the first in the list
        if position_index == 0:
            action_move_up.setEnabled(False)

        # Disable the move down action if the element is the last in the list
        if position_index == len(self.element.parent.get_descendants()) - 1:
            action_move_down.setEnabled(False)

        # Disable both actions if the element is a document
        if PROTEUS_DOCUMENT in self.element.classes:
            action_move_up.setEnabled(False)
            action_move_down.setEnabled(False)

            action_move_down.setVisible(False)
            action_move_up.setVisible(False)

        return action_move_up, action_move_down

    # ---------------------------------------------------------------------
    # Method     : _create_sort_submenu
    # Description: Create the children sort submenu.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_sort_submenu(self) -> QMenu:

        # Create the children sort submenu
        submenu: QMenu = QMenu(_("document_tree.menu.action.sort_children"), self)

        sort_submenu_icon = Icons().icon(ProteusIconType.App, "context-menu-sort")
        submenu.setIcon(sort_submenu_icon)

        # Add reverse false action --------------------
        self.action_children_sort: QAction = QAction(
            _("document_tree.menu.action.sort_children_alphabetically"), self
        )

        self.action_children_sort.triggered.connect(
            lambda: self._controller.sort_object_children(self.element.id)
        )
        sort_icon = Icons().icon(ProteusIconType.App, "context-menu-alphabetical-sort")
        self.action_children_sort.setIcon(sort_icon)

        submenu.addAction(self.action_children_sort)

        # Add reverse true action ---------------------
        self.action_children_sort_reverse: QAction = QAction(
            _("document_tree.menu.action.sort_children_reverse"), self
        )

        self.action_children_sort_reverse.triggered.connect(
            lambda: self._controller.sort_object_children(self.element.id, reverse=True)
        )

        sort_reverse_icon = Icons().icon(
            ProteusIconType.App, "context-menu-reverse-alphabetical-sort"
        )
        self.action_children_sort_reverse.setIcon(sort_reverse_icon)

        submenu.addAction(self.action_children_sort_reverse)

        # Visibility and state restrictions ------------
        # Change submenu state if the element has less than 2 children
        if len(self.element.get_descendants()) < 2:
            submenu.setEnabled(False)

        return submenu

    # ---------------------------------------------------------------------
    # Method     : _create_edit_model_action
    # Description: Create the edit action.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_edit_model_action(self) -> QAction:
        """
        Create the edit model action.
        """
        action: QAction = QAction(_("document_tree.menu.action.edit_model"), self)
        action.triggered.connect(
            lambda: RawObjectEditor.create_dialog(
                object_id=self.element.id, controller=self._controller
            )
        )
        edit_icon = Icons().icon(ProteusIconType.App, "model_editor")
        action.setIcon(edit_icon)

        if not Config().app_settings.developer_features:
            action.setEnabled(False)
            action.setVisible(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_store_object_as_archetype_action
    # Description: Create the store object as archetype action.
    # Date       : 05/11/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_store_object_as_archetype_action(self) -> QAction:
        """
        Create the store object as archetype action.
        """
        action: QAction = QAction(
            _("document_tree.menu.action.store_object_as_archetype"), self
        )
        action.triggered.connect(
            lambda: CreateObjectArchetypeDialog.create_dialog(
                object_id=self.element.id, controller=self._controller
            )
        )
        store_icon = Icons().icon(ProteusIconType.App, "create-object-archetype")
        action.setIcon(store_icon)

        # Disable the action if the element is a document or not in developer mode
        if (
            not Config().app_settings.developer_features
            or PROTEUS_DOCUMENT in self.element.classes
        ):
            action.setEnabled(False)
            action.setVisible(False)

        return action

    # ---------------------------------------------------------------------
    # Method     : _create_store_document_as_archetype_action
    # Description: Create the store document as archetype action.
    # Date       : 05/11/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def _create_store_document_as_archetype_action(self) -> QAction:
        """
        Create the store document as archetype action.
        """
        action: QAction = QAction(
            _("document_tree.menu.action.store_document_as_archetype"), self
        )
        action.triggered.connect(
            lambda: CreateDocumentArchetypeDialog.create_dialog(
                document_id=self.element.id, controller=self._controller
            )
        )
        store_icon = Icons().icon(ProteusIconType.App, "create-document-archetype")
        action.setIcon(store_icon)

        # Disable the action if the element is not a document or not in developer mode
        if (
            not Config().app_settings.developer_features
            or PROTEUS_DOCUMENT not in self.element.classes
        ):
            action.setEnabled(False)
            action.setVisible(False)

        return action

    # ======================================================================
    # Dialog slots methods (connected to the component signals and helpers)
    # ======================================================================

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog (static)
    # Description: Handle the creation and display of the form window.
    # Date       : 18/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(
        controller: Controller, tree_widget: QTreeWidget, position: QPoint
    ) -> "ContextMenu":
        """
        Handle the creation and display of the form window.
        """
        menu = ContextMenu(tree_widget=tree_widget, controller=controller)
        menu.exec(tree_widget.viewport().mapToGlobal(position))
        return menu


# --------------------------------------------------------------------------
# Class: AvailableArchetypesMenu
# Description: Class for the PROTEUS application context menu.
# Date: 31/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class AvailableArchetypesMenu(QMenu, ProteusComponent):
    """
    Class for the PROTEUS application archetypes context menu. The menu
    shows available archetypes to clone in the selected object. Do not
    show all the posible archetypes, only the explicitly accepted by the
    selected object.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 31/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self,
        parent_id: ProteusID,
        class_name: str,
        archetype_list: List[Object],
        *args,
        **kwargs,
    ) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Store the page object and the controller instance.

        :param parent_id: Parent object id.
        :param class_name: Class name.
        :param archetype_list: List of available archetypes.
        """
        super(AvailableArchetypesMenu, self).__init__(*args, **kwargs)

        # Dependencies
        self.archetype_list = archetype_list
        self.parent_id = parent_id
        self.class_name = class_name

        # Action buttons
        self.action_buttons: Dict[ProteusID, QAction] = {}

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component.
    # Date       : 31/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component.
        """
        icon = Icons().icon(ProteusIconType.Archetype, self.class_name)

        self.setIcon(icon)
        translated_class_name: str = _(
            f"archetype.class.{self.class_name}", alternative_text=self.class_name
        )
        self.setTitle(
            _("document_tree.menu.action.add_archetype", translated_class_name)
        )

        # Create the actions
        for archetype in self.archetype_list:
            action: QAction = QAction(
                _(archetype.get_property(PROTEUS_NAME).value), self
            )
            icon = Icons().icon(ProteusIconType.Archetype, archetype.classes[-1])
            action.setIcon(icon)
            action.triggered.connect(
                lambda: self.create_object_from_archetype(archetype.id, self.parent_id)
            )

            # Store the action button
            self.action_buttons[archetype.id] = action

        # Add the actions to the context menu
        for action in self.action_buttons.values():
            self.addAction(action)


    def create_object_from_archetype(self, archetype_id: ProteusID, parent_id: ProteusID) -> None:
        """
        Create a new object from the provided archetype and parent.

        :param archetype_id: The archetype id to create the object from.
        :param parent_id: The parent id to create the object from.
        """
        self._controller.create_object(archetype_id, parent_id)

        if self._state_manager.last_cloned_archetype is not None:
            PropertyDialog.create_dialog(
                self._controller,
                self._state_manager.last_cloned_archetype,
                True,
            )
