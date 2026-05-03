# ==========================================================================
# File: events.py
# Description: Events for the Proteus base application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from threading import Lock
import logging
from typing import Callable

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: ProteusEvent
# Description: Class for the events in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
# Singleton-per-subclass via __new__ with double-checked locking; QObject is
# initialized exactly once at instance creation. __init__ is intentionally
# empty so repeated XxxEvent() calls only pay a single attribute check.
#
# This shape replaces an earlier design that combined metaclass=AbstractObjectMeta
# (QObject's sip metaclass × ABCMeta), ABC abstract methods, and a re-entry
# guard inside __init__. That setup overflowed Windows' 1 MB main-thread C
# stack on Python 3.12/3.13 the first time any event was instantiated. Since
# every subclass already implements notify/connect and no third-party
# subclasses exist, ABC enforcement was dropped in favour of a flatter layout.
class ProteusEvent(QObject):
    """
    Base class for the events in the PROTEUS application.

    Events are defined as singletons, so only one instance per subclass can
    exist for the lifetime of the process. Each subclass declares its own
    `signal = pyqtSignal(...)` with a type-specific signature plus typed
    `notify(...)` and `connect(...)` wrappers around it.

    Concurrency: instance creation is protected by a class-level lock
    (double-checked locking). Subsequent calls hit the cached singleton
    with no lock acquisition.
    """

    # Singleton instance (per-subclass via name mangling: _ProteusEvent__instance)
    __instance = None
    # Shared lock across all event subclasses; only contended on first creation.
    __lock = Lock()

    # --------------------------------------------------------------------------
    # Method: __new__
    # Description: Singleton constructor + one-shot QObject initialisation.
    # Date: 31/12/2023
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):
        """
        Returns the cached singleton for `cls`, creating and initialising it
        on first access. Uses double-checked locking so the lock is only
        contended the first time any event of this subclass is created.
        """
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    instance = super().__new__(cls)
                    QObject.__init__(instance)
                    cls.__instance = instance
        return cls.__instance

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: No-op; QObject.__init__ already ran once in __new__.
    # Date: 31/12/2023
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        # Python calls __init__ on every constructor invocation, so this
        # MUST be a no-op for the singleton to behave correctly. Initialisation
        # happens exactly once inside __new__.
        pass

    # --------------------------------------------------------------------------
    # Method: notify
    # Description: Notify the event to connected methods. Subclasses override.
    # Date: 31/12/2023
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def notify(self, *args, **kwargs) -> None:
        """
        Emit the event's signal. Must be overridden by every concrete subclass
        with the correct argument signature.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement notify()"
        )

    # --------------------------------------------------------------------------
    # Method: connect
    # Description: Connect a listener to the event. Subclasses override.
    # Date: 31/12/2023
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def connect(self, method: Callable) -> None:
        """
        Connect a callable to the event's signal. Must be overridden by every
        concrete subclass with a properly typed callable signature.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement connect()"
        )


# --------------------------------------------------------------------------
# Class: OpenProjectEvent
# Description: Class for the open project event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class OpenProjectEvent(ProteusEvent):
    """
    Event to handle the opening of a project in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that a project has been opened.
        """
        log.debug("Emitting OPEN PROJECT EVENT signal...")

        self.signal.emit()

    def connect(self, method: Callable[[], None]) -> None:
        """
        Connect a method to the open project event. Signal do not emit any
        arguments.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: SaveProjectEvent
# Description: Class for the save project event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SaveProjectEvent(ProteusEvent):
    """
    Event to handle the saving of a project in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that a project has been saved.
        """
        log.debug("Emitting SAVE PROJECT EVENT signal...")

        self.signal.emit()

    def connect(cls, method: Callable[[], None]) -> None:
        """
        Connect a method to the save project event. Signal do not emit any
        arguments.

        :param method: The method to connect to the event.
        """
        cls.signal.connect(method)


# --------------------------------------------------------------------------
# Class: AddDocumentEvent
# Description: Class for the add document event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class AddDocumentEvent(ProteusEvent):
    """
    Event to handle the addition of a document in the PROTEUS application.
    """

    signal = pyqtSignal([str, int])

    def notify(self, document_id: ProteusID, position: int = None) -> None:
        """
        Notify the event that a document has been added. Receives the id of
        the document that has been added and the position of the new document.
        If no position is provided, the document is added at the end of the
        documents list.

        :param document_id: The id of the document that has been added.
        :param position: The position of the document in the documents list.
        """
        log.debug(
            f"Emitting ADD DOCUMENT EVENT signal... | document_id: {document_id}, position: {position}"
        )

        assert (
            document_id is not None or document_id != ""
        ), "Document id cannot be None or empty"

        self.signal.emit(document_id, position)

    def connect(self, method: Callable[[ProteusID, int], None]) -> None:
        """
        Connect a method to the add document event. The method should take two
        arguments: the id of the document that has been added and the position
        of the document in the documents list. Document position may be None.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: DeleteDocumentEvent
# Description: Class for the delete document event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DeleteDocumentEvent(ProteusEvent):
    """
    Event to handle the deletion of a document in the PROTEUS application.
    """

    signal = pyqtSignal([str])

    def notify(self, document_id: ProteusID) -> None:
        """
        Notify the event that a document has been deleted. Receives the id of
        the document that has been deleted.

        :param document_id: The id of the document that has been deleted.
        """
        log.debug(
            f"Emitting DELETE DOCUMENT EVENT signal... | document_id: {document_id}"
        )

        assert (
            document_id is not None or document_id != ""
        ), "Document id cannot be None or empty"

        self.signal.emit(document_id)

    def connect(self, method: Callable[[ProteusID], None]) -> None:
        """
        Connect a method to the delete document event. The method should take
        one argument: the id of the document that has been deleted.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: ModifyDocumentEvent
# Description: Class for the modify document event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ModifyObjectEvent(ProteusEvent):
    """
    Event to handle the modification of an object in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, object_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that an object has been modified. Receives the id of
        the object that has been modified and a boolean indicating whether the
        view should be updated.

        :param object_id: The id of the object that has been modified.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting MODIFY OBJECT EVENT signal... | object_id: {object_id} update_view: {update_view}"
        )

        assert (
            object_id is not None or object_id != ""
        ), "Object id cannot be None or empty"

        self.signal.emit(object_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the modify object event. The method should take
        two arguments: the id of the object that has been modified and a
        boolean indicating whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: AddObjectEvent
# Description: Class for the add object event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class AddObjectEvent(ProteusEvent):
    """
    Event to handle the addition of an object in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, object_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that an object has been added. Receives the id of
        the object that has been added and a boolean indicating whether the
        view should be updated.

        :param object_id: The id of the object that has been added.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting ADD OBJECT EVENT signal... | object_id: {object_id} update_view: {update_view}"
        )

        assert (
            object_id is not None or object_id != ""
        ), "Object id cannot be None or empty"

        self.signal.emit(object_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the add object event. The method should take
        two arguments: the id of the object that has been added and a
        boolean indicating whether the view should be updated.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: DeleteObjectEvent
# Description: Class for the delete object event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DeleteObjectEvent(ProteusEvent):
    """
    Event to handle the deletion of an object in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, object_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that an object has been deleted. Receives the id of
        the object that has been deleted and a boolean indicating whether the
        view should be updated.

        :param object_id: The id of the object that has been deleted.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting DELETE OBJECT EVENT signal... | object_id: {object_id} update_view: {update_view}"
        )

        assert (
            object_id is not None or object_id != ""
        ), "Object id cannot be None or empty"

        self.signal.emit(object_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the delete object event. The method should take
        two arguments: the id of the object that has been deleted and a
        boolean indicating whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: ChangeObjectPositionEvent
# Description: Class for the change object position event in the PROTEUS application.
# Date: 20/06/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ChangeObjectPositionEvent(ProteusEvent):
    """
    Event to handle the change of the position of an object in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, object_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that the position of an object has changed. Receives the id of
        the object that has changed position and a boolean indicating whether the view
        should be updated.

        :param object_id: The id of the object that has been moved.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting CHANGE OBJECT POSITION EVENT signal... | object_id: {object_id} update_view: {update_view}"
        )

        assert (
            object_id is not None or object_id != ""
        ), "Object id cannot be None or empty"

        self.signal.emit(object_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the change object position event. The method should take
        two arguments: the id of the object that has changed position and a
        boolean indicating whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: SortChildrenEvent
# Description: Class for the sort children event in the PROTEUS application.
# Date: 20/06/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SortChildrenEvent(ProteusEvent):
    """
    Event to handle the sorting of children in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, parent_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that the children of an object/document have been sorted.
        Receives the id of the parent object and a boolean indicating whether the view
        should be updated.

        :param parent_id: The id of the parent object.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting SORT CHILDREN EVENT signal... | parent_id: {parent_id} update_view: {update_view}"
        )

        assert (
            parent_id is not None or parent_id != ""
        ), "Parent id cannot be None or empty"

        self.signal.emit(parent_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the sort children event. The method should take
        two arguments: the id of the parent object and a boolean indicating
        whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: SelectObjectEvent
# Description: Class for the select object event in the PROTEUS application.
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SelectObjectEvent(ProteusEvent):
    """
    Event to handle the selection of an object in the PROTEUS application.
    """

    signal = pyqtSignal([str, str, bool, QTreeWidget.ScrollHint])

    def notify(
        self,
        selected_object_id: ProteusID | None,
        document_id: ProteusID,
        navigate: bool = True,
        scroll_behavior: QTreeWidget.ScrollHint = QTreeWidget.ScrollHint.EnsureVisible,
    ) -> None:
        """
        Notify the event that an object has been selected. Receives the id of
        the object that has been selected, the id of the document that contains
        the object and a boolean indicating whether the scroll should be performed.

        :param selected_object_id: The id of the object that has been selected.
        :param document_id: The id of the document that contains the object.
        :param navigate: Whether the view should navigate to the selected object.
        :param scroll_behavior: The scroll behavior to use when selecting the object in the document tree.
        """
        log.debug(
            f"Emitting SELECT OBJECT EVENT signal... | selected_object_id: {selected_object_id} document_id: {document_id} navigate: {navigate} scroll_behavior: {scroll_behavior}"
        )

        # NOTE: Object id can be None if the selection is cleared, see the
        # state_manager deselect_object method for more information.
        if selected_object_id is None:
            navigate = False

        assert (
            document_id is not None or document_id != ""
        ), "Document id cannot be None or empty"

        self.signal.emit(selected_object_id, document_id, navigate, scroll_behavior)

    def connect(self, method: Callable[[ProteusID, ProteusID], None]) -> None:
        """
        Connect a method to the select object event. The method should take
        two arguments: the id of the object that has been selected and the
        id of the document that contains the object.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: CurrentDocumentChangedEvent
# Description: Class for the current document changed event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class CurrentDocumentChangedEvent(ProteusEvent):
    """
    Event to handle the change of the current document in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, document_id: ProteusID, update_view: bool = True) -> None:
        """
        Notify the event that the current document has changed. Receives the id of
        the new current document and a boolean indicating whether the view should
        be updated.

        :param document_id: The id of the new current document.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting CURRENT DOCUMENT CHANGED EVENT signal... | document_id: {document_id} update_view: {update_view}"
        )

        # NOTE: Document id can be None if the current document is cleared.

        self.signal.emit(document_id, update_view)

    def connect(self, method: Callable[[ProteusID, bool], None]) -> None:
        """
        Connect a method to the current document changed event. The method should
        take two arguments: the id of the new current document and a boolean
        indicating whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: CurrentViewChangedEvent
# Description: Class for the current view changed event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class CurrentViewChangedEvent(ProteusEvent):
    """
    Event to handle the change of the current view in the PROTEUS application.
    """

    signal = pyqtSignal([str, bool])

    def notify(self, view_name: str, update_view: bool = True) -> None:
        """
        Notify the event that the current view has changed. Receives the name of
        the new current view and a boolean indicating whether the view should
        be updated.

        :param view_name: The name of the new current view.
        :param update_view: Whether the view should be updated.
        """
        log.debug(
            f"Emitting CURRENT VIEW CHANGED EVENT signal... | view_name: {view_name} update_view: {update_view}"
        )

        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty"

        self.signal.emit(view_name, update_view)

    def connect(self, method: Callable[[str, bool], None]) -> None:
        """
        Connect a method to the current view changed event. The method should
        take two arguments: the name of the new current view and a boolean
        indicating whether the view should be updated.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: StackChangedEvent
# Description: Class for the stack changed event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class StackChangedEvent(ProteusEvent):
    """
    Event to handle the change of the stack in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that the stack has changed.
        """
        log.debug("Emitting STACK CHANGED EVENT signal...")

        self.signal.emit()

    def connect(self, method: Callable[[], None]) -> None:
        """
        Connect a method to the stack changed event. The method should
        take no arguments.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: ClipboardChangedEvent
# Description: Class for the clipboard changed event in the PROTEUS
# Date: 31/07/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ClipboardChangedEvent(ProteusEvent):
    """
    Event to handle the changes of the clipboard in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that the clipboard has changed.
        """
        log.debug("Emitting CLIPBOARD CHANGED EVENT signal...")

        self.signal.emit()

    def connect(self, method: Callable[[], None]) -> None:
        """
        Connect a method to the clipboard changed event. The method should
        take no arguments.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)

# --------------------------------------------------------------------------
# Class: RequiredSaveActionEvent
# Description: Class for the required save action event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class RequiredSaveActionEvent(ProteusEvent):
    """
    Event to handle the required save action in the PROTEUS application.
    """

    signal = pyqtSignal(bool)

    def notify(self, save_required: bool = True) -> None:
        """
        Notify the event if a save action is required (project has unsaved
        changes). Receives a boolean indicating whether a save action is
        required.

        :param save_required: Whether a save action is required.
        """
        log.debug(
            f"Emitting REQUIRED SAVE ACTION EVENT signal... | save_required: {save_required}"
        )

        # TODO: This is a workaround to avoid RuntimeError when running all the tests with pytest command.
        # RuntimeError does not affect tests results but it makes the GitHub Actions workflow fail.
        # `RuntimeError: wrapped C/C++ object of type RequiredSaveActionEvent has been deleted`
        # This only happens in this specific event. Further investigation is needed.
        try:
            self.signal.emit(save_required)
        except RuntimeError as e:
            log.error(f"Error emitting REQUIRED SAVE ACTION EVENT signal: {e}")

    def connect(self, method: Callable[[bool], None]) -> None:
        """
        Connect a method to the required save action event. The method should
        take one argument: a boolean indicating whether a save action is
        required.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: AddViewEvent
# Description: Class for the add view event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class AddViewEvent(ProteusEvent):
    """
    Event to handle the addition of a view in the PROTEUS application.
    """

    signal = pyqtSignal([str])

    def notify(self, view_name: str) -> None:
        """
        Notify the event that a view has been added. Receives the name of
        the view that has been added.

        :param view_name: The name of the view that has been added.
        """
        log.debug(f"Emitting ADD VIEW EVENT signal... | view_name: {view_name}")

        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty"

        self.signal.emit(view_name)

    def connect(self, method: Callable[[str], None]) -> None:
        """
        Connect a method to the add view event. The method should take
        one argument: the name of the view that has been added.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: DeleteViewEvent
# Description: Class for the delete view event in the PROTEUS
# Date: 31/12/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DeleteViewEvent(ProteusEvent):
    """
    Event to handle the deletion of a view in the PROTEUS application.
    """

    signal = pyqtSignal([str])

    def notify(self, view_name: str) -> None:
        """
        Notify the event that a view has been deleted. Receives the name of
        the view that has been deleted.

        :param view_name: The name of the view that has been deleted.
        """
        log.debug(f"Emitting DELETE VIEW EVENT signal... | view_name: {view_name}")

        assert (
            view_name is not None or view_name != ""
        ), "View name cannot be None or empty"

        self.signal.emit(view_name)

    def connect(self, method: Callable[[str], None]) -> None:
        """
        Connect a method to the delete view event. The method should take
        one argument: the name of the view that has been deleted.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: UpdateMetricsEvent
# Description: Class for the update metrics event in the PROTEUS
# Date: 01/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class UpdateMetricsEvent(ProteusEvent):
    """
    Event to handle the update of the application metrics in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that the application metrics have been updated.
        """
        log.debug("Emitting UPDATE METRICS EVENT signal...")

        self.signal.emit()

    def connect(self, method: Callable[[], None]) -> None:
        """
        Connect a method to the update metrics event. The method should
        take no arguments.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)


# --------------------------------------------------------------------------
# Class: ArchetypeRepositoryChangedEvent
# Description: Class for the archetype repository changed event in the PROTEUS
# Date: 30/10/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ArchetypeRepositoryChangedEvent(ProteusEvent):
    """
    Event to handle the change of the archetype repository in the PROTEUS application.
    """

    signal = pyqtSignal()

    def notify(self) -> None:
        """
        Notify the event that the archetype repository has changed.
        """
        log.debug("Emitting ARCHETYPE REPOSITORY CHANGED EVENT signal...")

        self.signal.emit()

    def connect(self, method: Callable[[], None]) -> None:
        """
        Connect a method to the archetype repository changed event. The method should
        take no arguments.

        :param method: The method to connect to the event.
        """
        self.signal.connect(method)
