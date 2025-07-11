# ==========================================================================
# File: state_manager.py
# Description: State manager for the PROTEUS application. It managed the
#              state of the application, incluiding the current document,
#              the current object and the current view.
# Date: 19/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict, Union, List
from pathlib import Path
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QTreeWidget

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.application.utils.abstract_meta import SingletonMeta
from proteus.application.events import (
    SelectObjectEvent,
    CurrentDocumentChangedEvent,
    CurrentViewChangedEvent,
)

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: StateManager
# Description: State manager for the PROTEUS application.
# Date: 19/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class StateManager(metaclass=SingletonMeta):
    """
    State manager for the PROTEUS application. It stores the current
    selected document, the selected object for each document tree and the
    current view. Also stores the current project path.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Constructor for StateManager class.
    # Date: 15/11/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self):
        """
        It initializes the StateManager class.
        """

        # Instance variables
        self.current_document: ProteusID = None
        self.current_object: Dict[ProteusID, ProteusID] = {}
        self.current_view: str = None
        self.last_cloned_archetype: ProteusID = None

        self.current_project_path: Path = None

        self.opened_views: List[str] = []

    # ==========================================================================
    # App state variables management mehtods
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: set_current_document
    # Description: Sets the current document id.
    # Date: 19/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_current_document(
        self, document_id: ProteusID, update_view: bool = True
    ) -> None:
        """
        Sets the current document id and notifies that the current document
        has changed.

        :param document_id: Current document id
        """
        log.debug(f"Setting current document '{document_id}'")
        self.current_document = document_id

        # If the current document is not in the current object dictionary,
        # add it.
        if document_id not in self.current_object:
            self.current_object[document_id] = None

        # Notify the current document has changed
        CurrentDocumentChangedEvent().notify(self.current_document, update_view)

        # Force object selection on document change
        current_object = self.get_current_object()
        SelectObjectEvent().notify(current_object, document_id)

    # --------------------------------------------------------------------------
    # Method: get_current_document
    # Description: Returns the current document id.
    # Date: 19/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_current_document(self) -> Union[ProteusID, None]:
        """
        Returns the current document id. If no document is selected, it returns
        None.

        :return: Current document id
        :rtype: ProteusID or None
        """
        return self.current_document

    # --------------------------------------------------------------------------
    # Method: set_current_object
    # Description: Sets the current object id for the current document.
    # Date: 19/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_current_object(
        self,
        object_id: ProteusID,
        document_id: ProteusID,
        navigate: bool = True,
        scroll_behavior: QTreeWidget.ScrollHint = QTreeWidget.ScrollHint.EnsureVisible,
    ) -> None:
        """
        Sets the current object id for the document id and notifies that the
        selected object has changed for the given document.

        :param object_id: Selected object id
        :param document_id: Document that contains the selected object id
        :param navigate: Flag to indicate if we should navigate to the object in the view
        :param scroll_behavior: Scroll behavior when navigating to the object in the document tree
        """
        log.debug(f"Selecting object '{object_id}' in document '{document_id}'")

        assert (
            document_id in self.current_object
        ), f"Document id '{document_id}' not found in current application state dictionary."

        self.current_object[document_id] = object_id
        SelectObjectEvent().notify(object_id, document_id, navigate, scroll_behavior)

    # --------------------------------------------------------------------------
    # Method: get_current_object
    # Description: Returns the current object id for the current document.
    # Date: 19/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_current_object(self) -> Union[ProteusID, None]:
        """
        Returns the current object id for the current document. If no object
        or document is selected, it returns None.

        :return: Current object id
        :rtype: ProteusID or None
        """
        document_id = self.get_current_document()

        # If no document is selected, return None.
        if document_id is None:
            return None

        assert (
            document_id in self.current_object
        ), f"Document id {document_id} not found in current application state dictionary."

        return self.current_object[document_id]

    # --------------------------------------------------------------------------
    # Method: deselect_object
    # Description: Deselects the current object if found selected in the state
    #              manager dictionary.
    # Date: 21/06/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # NOTE: This method is primarily used when objects are marked as deleted
    #       (DEAD) when controller commands are executed.
    def deselect_object(self, object_id: ProteusID) -> None:
        """
        Deselects the current object if found selected in the state manager
        dictionary. If the object is not selected, it does nothing.

        If the object is deselected, it notifies that the selected object has
        changed for the document where the object was selected.

        :param object_id: Object id to deselect
        """
        for document_id in self.current_object:
            if self.current_object[document_id] == object_id:
                self.current_object[document_id] = None
                SelectObjectEvent().notify(None, document_id)

    # --------------------------------------------------------------------------
    # Method: set_current_view
    # Description: Sets the current view id.
    # Date: 03/07/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_current_view(self, view_name: str, update_view: bool = True) -> None:
        """
        Sets the current view id. Notifies the current view has changed.

        :param view_name: Current view id
        """
        log.debug(f"Setting current view '{view_name}'")

        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty."

        self.current_view = view_name

        # Notify the event manager that the current view has changed.
        CurrentViewChangedEvent().notify(self.current_view, update_view)

    # --------------------------------------------------------------------------
    # Method: get_current_view
    # Description: Returns the current view id.
    # Date: 03/07/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_current_view(self) -> Union[str, None]:
        """
        Returns the current view id. If no view is selected, it returns None.

        :return: Current view id
        :rtype: str or None
        """
        return self.current_view

    # --------------------------------------------------------------------------
    # Method: get_document_by_object
    # Description: Returns the document id where the given object id is selected.
    # Date: 20/12/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_document_by_object(self, object_id: ProteusID) -> Union[ProteusID, None]:
        """
        Returns the document id where the given object id is selected. If the
        object is not selected in any document, it returns None.

        :param object_id: object id
        :return: document id
        :rtype: ProteusID or None
        """
        for document_id in self.current_object:
            if self.current_object[document_id] == object_id:
                return document_id
        return None

    # --------------------------------------------------------------------------
    # Method: add_opened_view
    # Description: Adds the opened view to the opened views list.
    # Date: 04/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def add_opened_view(self, view_name: str) -> None:
        """
        Adds the opened view to the opened views list.

        :param view_name: Opened view name
        """

        # Check if the view name is not None or empty
        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty."

        # Check if the view is already opened
        if view_name in self.opened_views:
            log.error(f"View '{view_name}' is already opened.")
            return

        log.debug(f"Adding opened view '{view_name}' to the opened views list.")

        self.opened_views.append(view_name)

    # --------------------------------------------------------------------------
    # Method: remove_opened_view
    # Description: Removes the opened view from the opened views list.
    # Date: 04/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def remove_opened_view(self, view_name: str) -> None:
        """
        Removes the opened view from the opened views list.

        :param view_name: Opened view name
        """

        # Check if the view name is not None or empty
        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty."

        # Check if the view is already opened
        if view_name not in self.opened_views:
            log.error(f"View '{view_name}' is not in the opened views list.")
            return
        
        log.debug(f"Removing opened view '{view_name}' from the opened views list.")

        self.opened_views.remove(view_name)

    # ==========================================================================
    # State manager general methods
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: clear
    # Description: Clears the current state manager.
    # Date: 15/11/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def clear(self) -> None:
        """
        Clears the current state manager. It resets the current document,
        current object and current view.
        """
        log.debug("Clearing state manager")
        self.current_document = None
        self.current_object = {}
        self.current_view = None
        self.current_project_path = None
        self.last_cloned_archetype = None
        self.opened_views = []
