# ==========================================================================
# File: project_container.py
# Description: PyQT6 documents container component for the PROTEUS application
# Date: 25/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict, List
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QTabWidget, QWidget
from PyQt6.QtCore import QSize

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_ACRONYM
from proteus.model.object import Object
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.document_tree import DocumentTree
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.themes import Themes
from proteus.application.events import (
    AddDocumentEvent,
    ModifyObjectEvent,
    CurrentDocumentChangedEvent,
    DeleteDocumentEvent,
    ThemeChangedEvent,
)

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: DocumentsContainer
# Description: PyQT6 documents container class for the PROTEUS
#              application
# Date: 25/05/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DocumentsContainer(QTabWidget, ProteusComponent):
    """
    Documents tab menu component for the PROTEUS application. It is used to
    display the documents of the project in a tab menu. It manages the
    creation of the document tree component for each document.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, parent: QWidget, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.

        Store the tabs for each document in a dictionary to access them
        later.

        :param parent: Parent widget.
        """
        super(DocumentsContainer, self).__init__(parent, *args, **kwargs)

        # Tabs dictionary
        self.tabs: Dict[ProteusID, DocumentTree] = {}

        # Create the component
        self.create_component()

        # Subscribe to events
        self.subscribe()

        # Call the current document changed method to update the document for the
        # first time
        if len(self.tabs) > 0:
            self.current_document_changed(index=0)

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the documents tab menu component
    # Date       : 25/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the documents tab menu component. It gets the project
        structure from the controller and creates a tab for each
        document.
        """
        self.setObjectName("documents_container")
        icon_size: int = Themes().metric("icon_size_tab", 32)
        self.setIconSize(QSize(icon_size, icon_size))
        self.tabBar().setExpanding(True)

        # Handle tab reordering
        self.setMovable(True)
        self.tabBar().tabMoved.connect(self.tab_moved)

        # Get project structure from project service
        project_structure: List[Object] = self._controller.get_project_structure()

        # Add a document tab for each document in the project
        for document in project_structure:
            self.add_document(document)

        # Connect singal to handle document tab change
        self.currentChanged.connect(self.current_document_changed)

        log.info("Documents container tab component created")

    # ----------------------------------------------------------------------
    # Method     : add_document
    # Description: Add a document to the tab menu creating its child
    #              components (tree and render).
    # Date       : 25/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_document(self, document: Object, position: int = None) -> None:
        """
        Add a document to the tab menu creating its child component (document
        tree). If no position is given, the document is added at the end of
        the tab menu.

        :param document: Document to add to the tab menu.
        :param position: Position to add the document in the tab menu.
        """
        # Tree widget --------------------------------------------------------
        tab: DocumentTree = DocumentTree(self, document.id)

        # Add tab to the dictionary with the document id as key
        self.tabs[document.id] = tab

        # Get acronym, add the tab and store the index given by the addTab method
        document_acronym: str = document.get_property(PROTEUS_ACRONYM).value
        if position is not None:
            tab_index = self.insertTab(position, tab, document_acronym)
        else:
            tab_index = self.addTab(tab, document_acronym)

        # Set the tab icon
        icon = Icons().icon(ProteusIconType.Document, document_acronym)
        self.setTabIcon(tab_index, icon)
        icon_size: int = Themes().metric("icon_size_tab", 32)
        self.setIconSize(QSize(icon_size, icon_size))

        # Drop configuration to allow objects moves between tabs
        tabbar = self.tabBar()
        tabbar.setChangeCurrentOnDrag(True)
        tabbar.setAcceptDrops(True)

    # ----------------------------------------------------------------------
    # Method     : subscribe
    # Description: Subscribe the component to the events.
    # Date       : 15/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def subscribe(self) -> None:
        """
        Subscribe the component to the events.

        DocumentsContainer component subscribes to the following events:
            - ADD DOCUMENT -> update_on_add_document
            - MODIFY OBJECT -> update_on_modify_object
            - DELETE DOCUMENT -> update_on_delete_document
            - CURRENT DOCUMENT CHANGED -> update_on_current_document_changed
            - THEME CHANGED -> update_on_theme_changed
        """
        AddDocumentEvent().connect(self.update_on_add_document)
        ModifyObjectEvent().connect(self.update_on_modify_object)
        DeleteDocumentEvent().connect(self.update_on_delete_document)
        CurrentDocumentChangedEvent().connect(self.update_on_current_document_changed)
        ThemeChangedEvent().connect(self.update_on_theme_changed)

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_on_add_document
    # Description: Update the documents tab menu component when a new
    #              document is added to the project.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_add_document(self, new_document_id: ProteusID, position: int) -> None:
        """
        Update the documents tab menu component when a new document is added
        to the project. It creates a new tab for the document using the add
        document method. If no position is given, the document is added at
        the end of the tab menu.

        Triggered by: AddDocumentEvent

        :param new_document_id: New document id.
        :param position: Position to add the document in the tab menu.
        """
        # Check the element id is not None
        assert (
            new_document_id is not None or new_document_id != ""
        ), "Element id is None on ADD DOCUMENT event"

        # Get the new document
        new_document: Object = self._controller.get_element(new_document_id)

        # Check the document is instance of Object
        assert isinstance(
            new_document, Object
        ), "Object is not instance of Object on ADD_DOCUMENT event"

        self.add_document(new_document, position)

        # Set the current document to the new document
        self._state_manager.set_current_document(new_document_id)

    # ----------------------------------------------------------------------
    # Method     : update_on_delete_document
    # Description: Update the documents tab menu component when a document
    #              is deleted from the project.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_delete_document(self, document_id: ProteusID) -> None:
        """
        Update the documents tab menu component when a document is deleted
        from the project. It deletes the tab from the tabs widget and
        deletes the child components.

        Triggered by: DeleteDocumentEvent

        :param document_id: Id of the deleted document.
        """
        # Check the element id is not None or empty
        assert (
            document_id is not None or document_id != ""
        ), "Document id is None on DELETE OBJECT event"

        # Check there is a tab for the document
        assert (
            document_id in self.tabs
        ), f"Document tab not found for document {document_id} on DELETE_DOCUMENT event"

        # Delete tab from tabs widget and delete it
        document_tab: DocumentTree = self.tabs.pop(document_id)
        self.removeTab(self.indexOf(document_tab))
        document_tab.delete_component()

        # Delete tab object
        document_tab.parent = None
        document_tab.deleteLater()

    # ----------------------------------------------------------------------
    # Method     : update_on_modify_object
    # Description: Update the documents tab menu component when an object
    #              is modified.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_modify_object(self, object_id: ProteusID) -> None:
        """
        Update the documents tab menu component when an object is modified.
        It changes the tab name with the new document name if the object
        modified is a document.

        Triggered by: ModifyObjectEvent

        :param object_id: Id of the modified object.
        """
        # Check the element id is not None or empty
        assert (
            object_id is not None or object_id != ""
        ), "Element id is None on MODIFY OBJECT event"

        # Check if exists a tab for the element
        if object_id in self.tabs:
            # Get document tab
            document_tab: DocumentTree = self.tabs.get(object_id)
            tab_index: int = self.indexOf(document_tab)

            # Get new acronym
            element: Object = self._controller.get_element(object_id)
            document_acronym: str = element.get_property(PROTEUS_ACRONYM).value
            self.setTabText(tab_index, document_acronym)

            # Get new icon
            icon = Icons().icon(ProteusIconType.Document, document_acronym)
            self.setTabIcon(tab_index, icon)

    # ----------------------------------------------------------------------
    # Method     : update_on_current_document_changed
    # Description: Update the documents tab menu component when the current
    #              document is changed.
    # Date       : 20/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_current_document_changed(self, document_id: ProteusID) -> None:
        """
        Update the documents tab menu component when the current document
        is changed. It changes the current tab to the document tab with
        the current document id if the new current document is different
        from old current document.

        Triggered by: CurrentDocumentChangedEvent

        :param document_id: Id of the current selected document.
        """

        # Check if exists a tab for the element
        if document_id in self.tabs:
            # Get document tab
            document_tab: DocumentTree = self.tabs.get(document_id)
            tab_index: int = self.indexOf(document_tab)

            if tab_index != self.currentIndex():
                # Set current tab
                self.setCurrentIndex(tab_index)

    # ======================================================================
    # Component slots methods (connected to the component signals)
    # ======================================================================

    def update_on_theme_changed(self, theme_key: str) -> None:
        """
        Re-apply document tab icons and icon size when the application
        theme changes.

        Triggered by: ThemeChangedEvent

        :param theme_key: Key of the newly applied theme.
        """
        icon_size: int = Themes().metric("icon_size_tab", 32)
        self.setIconSize(QSize(icon_size, icon_size))

        for document_id, document_tab in self.tabs.items():
            tab_index: int = self.indexOf(document_tab)
            if tab_index < 0:
                continue

            document: Object = self._controller.get_element(document_id)
            document_acronym: str = document.get_property(PROTEUS_ACRONYM).value
            icon = Icons().icon(ProteusIconType.Document, document_acronym)
            self.setTabIcon(tab_index, icon)

    # ----------------------------------------------------------------------
    # Method     : current_document_changed
    # Description: Method triggered when the current document tab is changed.
    #              It updates the current document id in the state manager.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def current_document_changed(self, index: int) -> None:
        """
        Method triggered when the current document tab is changed. It updates
        the current document id in the state manager if the index is different
        from the current index.

        :param index: New tab index.
        """
        # Get document id
        document_id: ProteusID = None
        if index >= 0:
            # Access tab from the index
            document_tab: DocumentTree = self.widget(index)

            # Access document id (key) from the tab (value)
            tab_keys = list(self.tabs.keys())
            tab_values = list(self.tabs.values())
            tab_index = tab_values.index(document_tab)
            document_id: ProteusID = tab_keys[tab_index]

        # Avoid updating the state manager if the document is the same
        # This can happen when the tab is selected by current_document_changed
        # event
        if document_id == self._state_manager.get_current_document():
            return

        # Update current document in the state manager
        self._state_manager.set_current_document(document_id)

    # ----------------------------------------------------------------------
    # Method     : tab_moved
    # Description: Method triggered when a tab is moved. It updates the
    #              document position in the project.
    # Date       : 31/12/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def tab_moved(self, new_index: int, old_index: int) -> None:
        """
        Method triggered when a tab is moved. It updates the document position
        in the project.

        :param new_index: New tab index.
        :param old_index: Old tab index.
        """
        # Get the document id from the new index (tab has already been moved)
        document_tab: DocumentTree = self.widget(new_index)

        tab_keys = list(self.tabs.keys())
        tab_values = list(self.tabs.values())
        tab_index = tab_values.index(document_tab)
        document_id: ProteusID = tab_keys[tab_index]

        log.debug(f"Moving document {document_id} from {old_index} to {new_index}")

        # Index adjusting to allow pop and insert without problems
        if new_index > old_index:
            new_index += 1

        self._controller.change_document_position(document_id, new_index)
