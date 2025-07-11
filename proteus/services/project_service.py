# ==========================================================================
# File: project_service.py
# Description: Project interface
# Date: 06/05/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import Union, List, Dict, Set, Tuple

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports (starting from root)
# --------------------------------------------------------------------------

from proteus.model import (
    ProteusID,
    ID_ATTRIBUTE,
    CHILD_TAG,
    DOCUMENT_TAG,
    ProteusClassTag,
    PROTEUS_ANY,
    PROTEUS_NONE,
    PROTEUS_DOCUMENT,
    PROTEUS_NAME,
    PROTEUS_CODE,
    PROTEUS_DEPENDENCY,
    PROTEUS_AUTHOR,
    PROTEUS_WORKS_FOR,
    PROTEUS_INFORMATION_SOURCE,
)
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.abstract_object import ProteusState
from proteus.model.properties import Property, TraceProperty

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: ProjectService
# Description: Class for project operations interface
# Date: 06/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ProjectService:
    """
    Acts as an interface for project, documents and objects operations.
    Loads a project into memory and provides methods to perform operations.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor.
    # Date       : 07/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self):
        """
        Class constructor. Initializes the following instance variables:

        - project: Project object. It is initialized when the project is
        loaded via load_project method.

        - project_index: Dictionary with the project objects indexed by
        their id. It is initialized when the project is loaded via
        load_project method. Updated when get_element_by_id method is
        called via _populate_index method.

        - traces_index: Dictionary with the traces with the following
        structure: {key: target, value: set of tuples[source, trace type]}. It is initialized
        when the project is loaded via _load_traces_index method.
        """
        # Instance variables
        self.project: Project = None
        self.project_index: Dict[ProteusID, Union[Object, Project]] = {}
        self.traces_index: Dict[ProteusID, Set[Tuple[ProteusID, str]]] = {}

        log.info("ProjectService initialized.")

    # ----------------------------------------------------------------------
    # Method     : load_project
    # Description: Initializes the project service with the given project
    #              path.
    # Date       : 06/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def load_project(self, project_path: str):
        """
        Initializes the project service with the given project path. Force
        the load of every object in the project to store it in a dictionary
        for easy access.

        :param project_path: Path to the project directory.
        """
        # Load project
        self.project = Project.load(project_path)

        # Initialize project index
        self.project_index = {}

        # Populate project index
        self._populate_index()

        # Load traces index
        self._load_traces_index()

        log.info(f"Project '{self.project.get_property(PROTEUS_NAME).value}' loaded.")

    # ----------------------------------------------------------------------
    # Method     : _get_element
    # Description: Helper method that returns the project or object with
    #              the given id.
    # Date       : 06/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _get_element_by_id(self, element_id: ProteusID) -> Union[Project, Object]:
        """
        Returns the project or object with the given id.

        Raises an exception if the element is not found.

        :param element_id: Id of the project or object.
        :return: Project or object with the given id.
        """
        # Populate index to check for new objects
        if element_id not in self.project_index:
            self._populate_index()

        # Check if the element is in the index
        assert (
            element_id in self.project_index
        ), f"Element with id {element_id} not found."

        # Return the element
        return self.project_index[element_id]

    # ----------------------------------------------------------------------
    # Method     : _populate_index
    # Description: Helper method that populates the project index with
    #              the all the objects in the project. If an object was
    #              already in the index, it will be ignored.
    # Date       : 07/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _populate_index(self) -> None:
        """
        Populates the project index with the all the objects in the project.
        If an object was already in the index, it will be ignored.
        """

        def _populate_index_private(object: Object) -> None:
            """
            Private helper method that populates the project index with
            the all the objects in the project recursively.

            :param object: Object to add to the index.
            """
            # If the object is not in the index, add it
            if object.id not in self.project_index:
                self.project_index[object.id] = object

            # Add children to the index
            for child in object.get_descendants():
                _populate_index_private(child)

        # Load project index, this forces load for
        # every object in the project
        for document in self.project.get_descendants():
            _populate_index_private(document)

        # Include project in the index if it is not there
        if self.project.id not in self.project_index:
            self.project_index[self.project.id] = self.project

    # ----------------------------------------------------------------------
    # Method     : _load_traces_index
    # Description: Helper method that loads the traces index with the
    #              traces of all the objects in the project.
    # Date       : 27/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _load_traces_index(self) -> None:
        """
        Loads the traces index with the traces of all the objects in the
        project. This method loads the traces index from scratch, so it
        could impact performance.

        The traces index has the following structure: {key: target, value: set of sources}.
        This structure is the opposite of the one used in Traces, where the source
        contains a list of targets. This way is easier to check on delete operations.

        If a target is DEAD, it will be ignored in the traces index. This allows to
        the sources to be deleted. This is a consistency problem in the project.
        """
        # Initialize traces index
        self.traces_index = {}

        # Iterate over all objects in the project using the project index
        for object in self.project_index.values():
            # Skip project
            if object.id == self.project.id or object.state == ProteusState.DEAD:
                continue
            # Iterate over object's traces
            for trace in object.get_traces():
                # Include object in source set of all its targets
                for target in trace.value:
                    # Check if the target is exists or is DEAD
                    try:
                        target_object: Object = self._get_element_by_id(target)
                        assert (
                            target_object.state != ProteusState.DEAD
                        ), f"Target object '{target}' is DEAD."
                    except Exception as e:
                        log.error(
                            f"Found a Trace in object '{object.id}' targeting a DEAD object '{target}'. "
                            f"Target '{target}' will be ignored in load_traces_index method so it can be deleted. "
                            "Check for project inconsistencies, this might affect the project integrity. "
                            f"Error: {e}"
                        )
                        if target in self.traces_index:
                            self.traces_index.pop(target)

                    # Add object to the target's source set
                    if target not in self.traces_index:
                        self.traces_index[target] = set()
                    self.traces_index[target].add(tuple([object.id, trace.traceType]))

    # ----------------------------------------------------------------------
    # Method     : get_traces_dependencies
    # Description: Checks if the given object has traces pointing to it.
    # Date       : 27/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_traces_dependencies(
        self, object_id: ProteusID
    ) -> Dict[ProteusID, Set[ProteusID]]:
        """
        Checks if the given object and its children have traces pointing to them.
        Do not check for traces pointing to DEAD objects.

        :param object_id: Id of the object to check.
        :return: Dictionary with a set of sources ids pointing to each object.
        """

        object: Object = self._get_element_by_id(object_id)

        # Dictionary to store the sources by object id
        sources: Dict[ProteusID, Set] = {}

        # Skip if the object is DEAD
        if object.state == ProteusState.DEAD:
            return sources

        # Check if the object has traces pointing to it
        if object_id in self.traces_index:
            sources[object_id] = set(t[0] for t in self.traces_index[object_id])

        # Check if the object has children, for each child check
        # if it has traces pointing to it calling recursively
        for child in object.get_descendants():
            sources.update(self.get_traces_dependencies(child.id))

        return sources

    # ----------------------------------------------------------------------
    # Method     : get_traces_dependencies_outside
    # Description: Checks if the given object has traces pointing to it
    #              from outside the given object and its children.
    # Date       : 31/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_traces_dependencies_outside(
        self, object_id: ProteusID
    ) -> Dict[ProteusID, Set[ProteusID]]:
        """
        Checks if the given object and its children have traces pointing to them
        only from outside the given object and its children. Do not check for
        traces pointing to DEAD objects.

        :param object_id: Id of the object to check.
        :return: Dictionary with a set of sources ids pointing to each object.
        """
        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)
        children_ids: Set[ProteusID] = object.get_ids()

        # Dictionary to store the sources by object id
        traces_dependencies: Dict[ProteusID, Set[ProteusID]] = (
            self.get_traces_dependencies(object_id)
        )

        # Check if sources are inside the object, if so, remove them
        for target, sources in traces_dependencies.copy().items():
            for source in sources.copy():
                if source in children_ids:
                    sources.remove(source)

            # If there are no sources left, remove the target
            if not sources:
                traces_dependencies.pop(target)

        return traces_dependencies

    # ----------------------------------------------------------------------
    # Method     : get_properties
    # Description: Returns the project or object properties properties.
    # Date       : 06/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_properties(self, element_id: ProteusID) -> Dict[str, Property]:
        """
        Returns the project or object properties.

        :param element_id: Id of the project or object.
        :return: Dictionary of properties.
        """
        element = self._get_element_by_id(element_id)

        return element.properties

    # ----------------------------------------------------------------------
    # Method     : update_properties
    # Description: Updates the project or object properties.
    # Date       : 06/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_properties(
        self, element_id: ProteusID, properties: List[Property]
    ) -> None:
        """
        Updates the project or object properties.

        :param element_id: Id of the project or object.
        :param properties: List of properties to update.
        """
        # Check properties is a list
        assert isinstance(properties, list), "Properties must be a list."

        # Check properties are Property objects
        assert all(
            isinstance(property, Property) for property in properties
        ), "Properties must be Property objects."

        # Get element by id
        element = self._get_element_by_id(element_id)

        # Check element is an object or project
        assert isinstance(
            element, (Object, Project)
        ), f"Element with id {element_id} is not an object or project."

        # Discard TraceProperties that are not valid
        discarded_traces = []
        new_traces = []
        traces: List[TraceProperty] = [
            property for property in properties if isinstance(property, TraceProperty)
        ]
        for trace in traces:
            valid_targets = trace.value.copy()
            invalid_target_found_flag = False

            # Check if there is a trace to a DEAD object, DOCUMENT or the element itself to discard it
            for target_id in trace.value:
                try:
                    target = self._get_element_by_id(target_id)
                    if (
                        target.state == ProteusState.DEAD
                        or PROTEUS_DOCUMENT in target.classes
                        or target_id == element_id
                    ):
                        valid_targets.remove(target_id)
                        invalid_target_found_flag = True
                        log.warning(
                            f"TraceProperty '{trace.name}' from object '{element_id}' to target '{target_id}' was discarded because it is a DOCUMENT, it has DEAD state or it is the same object. "
                            f"Target is state is '{target.state}', target classes are '{target.classes}', target_id is '{target_id}' and element_id is '{element_id}'"
                        )
                except Exception as e:
                    valid_targets.remove(target_id)
                    invalid_target_found_flag = True

                    log.warning(
                        f"Trace from object '{element_id}' to target '{target_id}' was discarded because error: {e}."
                    )

            # Set the new targets if necessary
            if not valid_targets and invalid_target_found_flag:
                discarded_traces.append(trace)
                log.warning(
                    f"Trace from object '{element_id}' to target '{trace.value}' was discarded because all targets are DEAD or DOCUMENT."
                )
            elif len(valid_targets) < len(trace.value):
                modified_trace = trace.clone(new_targets=valid_targets)
                new_traces.append(modified_trace)
                discarded_traces.append(trace)

        # Pop discarded traces from properties list and add new traces
        for trace in discarded_traces:
            properties.remove(trace)

        properties.extend(new_traces)

        for property in properties:
            element.set_property(property)

        # If TraceProperties were modified, update traces index
        if len([p for p in properties if isinstance(p, TraceProperty)]) > 0:
            self._load_traces_index()

    # ----------------------------------------------------------------------
    # Method     : save_project
    # Description: Saves the project to disk.
    # Date       : 06/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_project(self) -> None:
        """
        Saves the project to disk.
        """
        self.project.save_project()

    # ----------------------------------------------------------------------
    # Method     : has_unsaved_changes
    # Description: Checks if the project has unsaved changes.
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def has_unsaved_changes(self) -> bool:
        """
        Checks if the project has unsaved changes.

        Iterates over the project index and checks if any object is not in
        CLEAN state. Returns True in the first object found with unsaved
        changes.

        NOTE: DEAD objects are not considered as unsaved changes. They are kept
        in the project index even if they are deleted. This will allow to restore
        delete objects in the future. This is not a problem because when an object
        is deleted its parent is set to DIRTY.

        :return: True if the project has unsaved changes, False otherwise.
        """
        for object in self.project_index.values():
            if object.state != ProteusState.CLEAN and object.state != ProteusState.DEAD:
                log.debug(
                    f"Found object '{object.id}' with unsaved changes. Object state: {object.state}"
                )
                return True

        return False

    # ----------------------------------------------------------------------
    # Method     : get_object_structure
    # Description: Returns the object structure as a tree.
    # Date       : 08/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_object_structure(self, object_id: ProteusID) -> Dict[Object, List]:
        """
        Returns the element structure as a tree. Each element is represented
        by a dictionary with the following structure: {id: [{id: [{...}, {...}, ...]}, {...}, ...]}.
        Each object is represented by a list of dictionaries, where each dictionary
        represents a child object. The list is empty if the object has no children.

        :param element_id: Id of the element.
        :return: Dictionary with the element structure.
        """
        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)

        # Initialize an empty dictionary to store the object structure
        obj_struc: Dict[Object, List] = {}

        # Create object structure
        obj_struc_list: List = self._get_object_structure(object)
        obj_struc[object] = obj_struc_list

        return obj_struc

    def _get_object_structure(self, object: Object) -> Dict[Object, List]:
        """
        Private method for get_object_structure.
        """
        # Check that the element is an object
        assert isinstance(object, Object), f"Element with id {object} is not an object."

        # Initialize an empty list to store the objects
        children_struc: List = list()

        # Add children to the structure
        for child in object.get_descendants():
            # Initialize an empty dictionary to store the current object structure
            obj_struc: Dict[Object, List] = {}

            # Create child structure
            child_struc: Dict[Object, List] = self._get_object_structure(child)
            obj_struc[child] = child_struc

            # Add child to the list
            children_struc.append(obj_struc)

        return children_struc

    # ----------------------------------------------------------------------
    # Method     : get_project_structure
    # Description: Returns the project structure one depth level.
    # Date       : 08/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_project_structure(self) -> List[Object]:
        """
        Returns the project structure one depth level. Documents are returned
        as a list of objects.

        :return: List with the project documents.
        :rtype: List[Object]
        """
        return self.project.get_descendants()

    # ----------------------------------------------------------------------
    # Method     : get_project_available_classes
    # Description: Returns the available classes in the project.
    # Date       : 06/02/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_project_available_classes(
        self, include_subclasses: bool = False
    ) -> Set[ProteusClassTag]:
        """
        Get all the available classes currently in the project. If include_subclasses
        is True, also include all the subclasses of the available.

        :param include_subclasses: Include subclasses of the available classes.
        """
        # Initialize an empty set for the classes
        classes: Set[ProteusClassTag] = set()

        # Iterate over all objects in the project
        for object in self.project_index.values():
            # Skip project and dead objects
            if object.state == ProteusState.DEAD or object.id == self.project.id:
                continue

            # Add object classes or main class to the set
            if include_subclasses:
                classes.update(object.classes)
            else:
                classes.add(object.classes[-1])

        # Remove special Proteus classes from the set if any
        classes.discard(PROTEUS_ANY)
        classes.discard(PROTEUS_NONE)
        classes.discard(PROTEUS_DOCUMENT)

        return sorted(classes)

    # ----------------------------------------------------------------------
    # Method     : get_project_available_trace_types
    # Description: Returns the available trace types in the project.
    # Date       : 18/11/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_project_available_trace_types(self) -> Set[str]:
        """
        Get all the available trace types currently in the project.

        :return: Set of available trace types.
        """
        # Initialize an empty set for the trace types
        trace_types: Set[str] = set()

        for traces in self.traces_index.values():
            for _, type in traces:
                trace_types.add(type)

        # Add default trace types
        trace_types.add(PROTEUS_INFORMATION_SOURCE)
        trace_types.add(PROTEUS_AUTHOR)
        trace_types.add(PROTEUS_WORKS_FOR)
        trace_types.add(PROTEUS_DEPENDENCY)
        return trace_types

    # ----------------------------------------------------------------------
    # Method     : get_objects
    # Description: Returns objects in the project.
    # Date       : 25/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_objects(self, classes: List[ProteusClassTag] = []) -> List[Object]:
        """
        Get the objects of the current project. They can be filtered by classes.
        If classes is empty, is None or contains :Proteus-any, return all objects.

        This method does not return :Proteus-document objects.

        :param classes: List of classes to filter objects.
        :type classes: List[ProteusClassTag]
        :return: List of objects.
        :rtype: List[Object]
        """

        # Variable initialization
        objects: List[Object] = []

        # if classes is empty, is None or contains :Proteus-any, return all objects
        if not classes or PROTEUS_ANY in classes:
            # Iterate over project index and drop project and dead objects
            for element in self.project_index.values():
                if (
                    isinstance(element, Object)
                    and element.state != ProteusState.DEAD
                    and PROTEUS_DOCUMENT not in element.classes
                ):
                    objects.append(element)

        # else, filter objects by classes droping project and dead objects
        else:
            object: Object
            # Iterate over all objects in the project
            for object in self.project_index.values():
                if (
                    object.state == ProteusState.DEAD
                    or not isinstance(object, Object)
                    or PROTEUS_DOCUMENT in object.classes
                ):
                    continue

                # Get object classes
                object_classes: List[ProteusClassTag] = object.classes

                # Check for common classes between object classes and desired classes
                common_classes = [c for c in classes if c in object_classes]
                if common_classes:
                    objects.append(object)

        return objects

    # ----------------------------------------------------------------------
    # Method     : clone_object
    # Description: Clones the object with the given id.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def clone_object(self, object_id: ProteusID, parent_id: ProteusID) -> None:
        """
        Clones the object with the given id into the parent object. If the
        parent object is the same as the object parent, the object is cloned
        in the next position of the original object.

        :param object_id: Id of the object to clone.
        :param parent_id: Id of the new parent object.
        """
        # Check the object_id is not None
        assert object_id is not None, "Object id cannot be None."

        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)

        # New parent
        new_parent: Union[Project, Object] = self._get_element_by_id(parent_id)

        # Check that the object is an object
        assert isinstance(object, Object), f"Element with id {object} is not an object."

        # Calculate position of the cloned object
        siblings: List[Object] = new_parent.get_descendants()
        if object in siblings:
            cloned_position: int = siblings.index(object) + 1
        else:
            cloned_position: int = len(siblings)

        # Clone object
        return object.clone_object(
            parent=new_parent, project=self.project, position=cloned_position
        )

    # ----------------------------------------------------------------------
    # Method     : change_object_position
    # Description: Changes the position of the object with the given id.
    # Date       : 13/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def change_object_position(
        self,
        object_id: ProteusID,
        new_parent_id: ProteusID,
        new_position: int | None = None,
    ) -> None:
        """
        Changes the position of the object with the given id. If position is
        None, the object is moved to the end of the parent. Given position
        must be relative to non DEAD objects.

        :param object_id: Id of the object to change position.
        :param new_parent: New parent of the object.
        :param new_position: New position of the object.
        """
        # Check the object_id and new_parent are valid
        assert isinstance(object_id, str), f"Invalid object id {object_id}."
        assert isinstance(new_parent_id, str), f"Invalid new parent id {new_parent_id}."

        # Get object and new parent using helper method
        object: Object = self._get_element_by_id(object_id)
        new_parent: Union[Project, Object] = self._get_element_by_id(new_parent_id)

        # Check that the object is an object and the new parent is an object or project
        assert isinstance(
            object, Object
        ), f"Element with id {object_id} is not an object but a {type(object)}."
        assert isinstance(
            new_parent, (Project, Object)
        ), f"Element with id {new_parent_id} is not an object or project."

        # Set old parent to change its state later
        old_parent: Union[Project, Object] = object.parent

        # Reorder descendants list in new and old parent to push all DEAD objects to the end
        def _reorder_descendants_list(parent: Union[Project, Object]) -> None:
            """
            Reorder object/project descendants pushing all DEAD objects to the end.

            :param parent: Parent object.
            """
            # Auxiliary lists
            non_dead_descendants: List[Object] = []
            dead_descendants: List[Object] = []

            for o in parent.get_descendants():
                if o.state == ProteusState.DEAD:
                    dead_descendants.append(o)
                else:
                    non_dead_descendants.append(o)

            new_parent_descendants: List[Object] = (
                non_dead_descendants + dead_descendants
            )
            if isinstance(parent, Project):
                parent._documents = new_parent_descendants
            elif isinstance(parent, Object):
                parent._children = new_parent_descendants

        _reorder_descendants_list(old_parent)
        _reorder_descendants_list(new_parent)

        # If new and old parent are the same, extra checks are needed
        if new_parent.id == old_parent.id:
            # Index will return the first occurrence of the object, we need to ensure
            # that the removed object is the one in the old position. This can be
            # achieved by starting the search from the current position
            # if the new position is lower than the current position (would appear
            # before and push the object one position forward)
            current_position: int = old_parent.get_descendants().index(object)
            start_looking_position: int = 0
            if new_position < current_position:
                start_looking_position = current_position

            new_parent.add_descendant(object, new_position)
            current_position_after_move: int = old_parent.get_descendants().index(
                object, start_looking_position
            )
            old_parent.get_descendants().pop(current_position_after_move)
        # If new and old parent are not the same, just move the object and remove it from the old parent
        else:
            old_parent.get_descendants().remove(object)
            new_parent.add_descendant(object, new_position)

            # Change state of old parent if it was CLEAN
            if old_parent.state == ProteusState.CLEAN:
                old_parent.state = ProteusState.DIRTY

    # ----------------------------------------------------------------------
    # Method     : check_position_change
    # Description: Check if an object can be moved to the given position.
    # Date       : 02/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def check_position_change(
        self,
        object_id: ProteusID,
        new_position: int,
        new_parent_id: ProteusID,
    ) -> bool:
        """
        Check if an object can be moved to the given position. Parent must
        accept the object as a child and position must be different from
        current position.

        :param object_id: Id of the object to change position.
        :param new_position: New position of the object.
        :param new_parent: New parent of the object.
        """
        # TODO: This method should be refactored to not recieve the new position
        #       relative to non DEAD objects, but relative to all objects. Since
        #       this is a problem when redoing delete operations.

        # Check the object_id is valid
        assert isinstance(object_id, str), f"Invalid object id {object_id}."

        # Check the new_parent is valid
        assert isinstance(new_parent_id, str), f"Invalid new parent id {new_parent_id}."

        # Get new parent using helper method
        new_parent: Union[Project, Object] = self._get_element_by_id(new_parent_id)

        # Check the new_parent is valid
        assert isinstance(
            new_parent, (Project, Object)
        ), f"Invalid new parent {new_parent}."

        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)

        # Check that the object is an object
        assert isinstance(object, Object), f"Element with id {object} is not an object."

        # Current position of the object in its parent
        current_position: int = object.parent.get_descendants().index(object)

        # Variable to store the result
        position_change_allowed: bool = True

        # The parent must accept the object as a child
        if not new_parent.accept_descendant(object):
            position_change_allowed = False
        # If the position is changing within the same parent avoid same position
        elif new_parent == object.parent:
            # Position must be different from current position
            if new_position == current_position or new_position == current_position + 1:
                position_change_allowed = False
            # If no position specified (default last) do not allow drop in the same parent
            elif new_position is None:
                position_change_allowed = False
            # Avoid new position to be last if the object is the last one
            elif (
                new_position >= len(object.parent.get_descendants())
                and current_position == len(object.parent.get_descendants()) - 1
            ):
                position_change_allowed = False
        # An object cannot be moved to its own children
        elif new_parent_id in object.get_ids():
            position_change_allowed = False

        return position_change_allowed

    # ----------------------------------------------------------------------
    # Method     : check_clone_operation
    # Description: Check if an object can be cloned in the given parent.
    # Date       : 15/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def check_clone_operation(
        self,
        object_id: ProteusID,
        new_parent_id: ProteusID,
    ) -> bool:
        """
        Check if an object can be cloned in the given parent.

        Returns True if the parent accepts the object as a descendant and the
        object can be cloned in the new parent. Returns False otherwise.
        Raises an exception if the object_id or new_parent_id are invalid.

        :param object_id: Id of the object to clone.
        :param new_parent_id: Id of the new parent.
        """
        # Check the object_id is valid
        assert isinstance(object_id, str), f"Invalid object id {object_id}."

        # Check the new_parent is valid
        assert isinstance(new_parent_id, str), f"Invalid new parent id {new_parent_id}."

        # Get new parent using helper method
        new_parent: Union[Project, Object] = self._get_element_by_id(new_parent_id)

        # Check the new_parent is valid
        assert isinstance(
            new_parent, (Project, Object)
        ), f"Invalid new parent {new_parent}."

        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)

        # Check that the object is an object
        assert isinstance(object, Object), f"Element with id {object} is not an object."

        # Check if the object can be cloned in the new parent
        paste_allowed: bool = new_parent.accept_descendant(object)

        return paste_allowed

    # ----------------------------------------------------------------------
    # Method     : generate_project_xml
    # Description: Generates the xml file for the given document.
    # Date       : 04/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def generate_project_xml(self) -> ET._Element:
        """
        Generates the xml file for the actual project. Iterates until no
        child tags are found. Replaces child tags with the xml of the child
        object or document.

        :return: Root element of the xml file.
        :rtype: ET._Element
        """
        # Generate project xml file
        root: ET._Element = self.project.generate_xml()
        # Iterate over document tag and replace the asked document
        for document_element in root.findall(f".//{DOCUMENT_TAG}"):
            parent_element: ET._Element = document_element.getparent()
            document_id: ProteusID = document_element.attrib[ID_ATTRIBUTE]
            document: Object = self._get_element_by_id(document_id)
            document_xml: ET._Element = document.generate_xml()
            parent_element.replace(document_element, document_xml)

        # Iterate until no chil tags are found
        while root.findall(f".//{CHILD_TAG}"):
            # Load children
            children = root.findall(f".//{CHILD_TAG}")

            # Parse object's children
            child_element: ET._Element
            for child_element in children:
                child_id: ProteusID = child_element.attrib[ID_ATTRIBUTE]

                # Get child object
                child: Object = self._get_element_by_id(child_id)

                # Remove dead objects
                if child.state == ProteusState.DEAD:
                    parent_element: ET._Element = child_element.getparent()
                    parent_element.remove(child_element)
                else:
                    # Generate xml file
                    child_xml: ET._Element = child.generate_xml()

                    # Replace child element with xml
                    parent_element: ET._Element = child_element.getparent()
                    parent_element.replace(child_element, child_xml)

        return root

    # ----------------------------------------------------------------------
    # Method     : sort_children_by_name
    # Description: Sort the children of the object by name.
    # Date       : 17/06/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def sort_children_by_name(
        self, object_id: ProteusID, reverse: bool = False
    ) -> None:
        """
        Sort the children of the object with the given id by name (:Proteus-name).
        Code (:Proteus-code) is added to as prefix if it is found in the object.

        :param object_id: Id of the object to sort.
        """
        # Get object using helper method
        object: Object = self._get_element_by_id(object_id)

        # Check that the element is an object
        assert isinstance(
            object, Object
        ), f"Element with id {object} is not an object but a {type(object)}."

        # Lambda expression to sort by name or code + name
        lambda_ = lambda child: (
            f"{child.get_property(PROTEUS_CODE).value.to_string()} {child.get_property(PROTEUS_NAME).value}"
            if child.get_property(PROTEUS_CODE)
            else child.get_property(PROTEUS_NAME).value
        )

        # Sort descendants by name
        object.children.sort(key=lambda_, reverse=reverse)

        # Update object state
        object.state = ProteusState.DIRTY
