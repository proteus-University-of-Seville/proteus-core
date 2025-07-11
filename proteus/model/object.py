# ==========================================================================
# File: object.py
# Description: a PROTEUS object
# Date: 16/09/2022
# Version: 0.2
# Author: Amador Durán Toro
# ==========================================================================
# Update: 16/09/2022 (Amador)
# Description:
# - Object now inherits from AbstractObject
# ==========================================================================
# Update: 15/04/2023 (José María)
# Description:
# - Object now lazy loads its children.
# ==========================================================================

# for using classes as return type hints in methods
# (this will change in Python 3.11)
from __future__ import annotations  # it has to be the first import

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import pathlib
import os
import logging
from typing import List, NewType, Union, Dict
import copy
import shutil
import datetime

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET
import shortuuid

# --------------------------------------------------------------------------
# Project specific imports (starting from root)
# --------------------------------------------------------------------------

from proteus.model import (
    ProteusID,
    PROTEUS_DATE,
    PROTEUS_CODE,
    PROTEUS_NAME,
    PROTEUS_DOCUMENT,
    ID_ATTRIBUTE,
    CLASSES_ATTRIBUTE,
    ACCEPTED_CHILDREN_ATTRIBUTE,
    ACCEPTED_PARENTS_ATTRIBUTE,
    SELECTED_CATEGORY_ATTRIBUTE,
    NUMBERED_ATTRIBUTE,
    CHILDREN_TAG,
    OBJECT_TAG,
    OBJECTS_REPOSITORY,
    CHILD_TAG,
    PROTEUS_ANY,
    ASSETS_REPOSITORY,
    COPY_OF,
)
from proteus.model.abstract_object import AbstractObject, ProteusState
from proteus.model.properties import (
    Property,
    FileProperty,
    DateProperty,
    CodeProperty,
    TraceProperty,
)
from proteus.model.properties.code_property import ProteusCode
from proteus.application.resources.translator import translate as _


# from proteus.model.project import Project
# Project class dummy declaration to break circular import
class Project(AbstractObject):
    pass


# Type for Class tags in Proteus
ProteusClassTag = NewType("ProteusClassTag", str)

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: Object
# Description: Class for PROTEUS objects
# Date: 16/09/2022
# Version: 0.2
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


class Object(AbstractObject):
    """
    A PROTEUS object is an XML file inside of a PROTEUS project 'objects'
    directory.

    A PROTEUS object can only be created by cloning another existing object,
    usually an archetype object.

    An already created object can be loaded by providing the path to its XML
    file.
    """

    # ----------------------------------------------------------------------
    # Method: load (static)
    # Description: It loads a PROTEUS object from disk into memory
    # Date: 16/09/2022
    # Version: 0.2
    # Author: Amador Durán Toro
    # ----------------------------------------------------------------------
    # NOTE: Current working directory is set by Project.load().
    #       Do not change current directory in this method.
    # ----------------------------------------------------------------------

    @staticmethod
    def load(id: ProteusID, project: Project) -> Object:
        """
        Static factory method for loading a PROTEUS object given a project
        and a short UUID.
        """
        # Check project is not None
        assert (
            project is not None
        ), f"Invalid project object when loading object from {id}.xml"

        # Extract project directory from project path
        project_directory: str = os.path.dirname(project.path)
        log.info(
            f"Loading a PROTEUS object from {project_directory}/{OBJECTS_REPOSITORY}/{id}.xml"
        )

        # Create path to objects repository
        objects_repository: str = f"{project_directory}/{OBJECTS_REPOSITORY}"

        # Check objects repository is a directory
        assert os.path.isdir(
            objects_repository
        ), f"PROTEUS projects must have an objects repository. {objects_repository} is not a directory."

        # Complete path to object file
        object_file_path = f"{objects_repository}/{id}.xml"

        # # Check if object file exists
        assert os.path.isfile(
            object_file_path
        ), f"PROTEUS object file {object_file_path} not found in {objects_repository}."

        # Create and return the project object
        return Object(object_file_path, project=project)

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: It initializes a PROTEUS object and builds it using an
    #              XML file.
    # Date       : 16/09/2022
    # Version    : 0.2
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------

    def __init__(self, object_file_path: str, project: Project = None) -> None:
        """
        It initializes and builds a PROTEUS object from an XML file.
        """
        # Initialize property dictionary in superclass
        # TODO: pass some arguments?
        super().__init__(object_file_path)

        if not os.path.isfile(object_file_path):
            self.state = ProteusState.FRESH

        # Save project as an object's attribute
        self.project: Project = project

        # Parse and load XML into memory
        root: ET._Element = ET.parse(object_file_path).getroot()

        # Check root tag is <object>
        assert (
            root.tag == OBJECT_TAG
        ), f"PROTEUS object file {object_file_path} must have <{OBJECT_TAG}> as root element, not {root.tag}."

        # Get object ID from XML
        self.id: ProteusID = ProteusID(root.attrib[ID_ATTRIBUTE])

        # Object or Project
        self.parent: Union[Object, Project] = None

        # Get object classes and accepted children classes
        self.classes: List[ProteusClassTag] = root.attrib[CLASSES_ATTRIBUTE].split()
        self.acceptedChildren: List[ProteusClassTag] = root.attrib[
            ACCEPTED_CHILDREN_ATTRIBUTE
        ].split()

        # Get accepted parent classes
        # NOTE: Prevent second level archetypes to be accepted by any archetypes.
        # Default value is PROTEUS_ANY, which means any object can be parent.
        self.acceptedParents: List[ProteusClassTag] = root.attrib.get(
            ACCEPTED_PARENTS_ATTRIBUTE, PROTEUS_ANY
        ).split()

        # Selected category provides information about which property category
        # is more relevant among the others to the user. It can be None
        self.selectedCategory: str = root.attrib.get(SELECTED_CATEGORY_ATTRIBUTE, "")

        # Numbered attribute (in children tag)
        # Tells if the children must be numbered when displayed
        children_element = root.find(CHILDREN_TAG)
        numbered_str = "false"
        if children_element is not None:
            numbered_str = children_element.attrib.get(NUMBERED_ATTRIBUTE, "false")
        self.numbered = True if numbered_str.lower() == "true" else False

        # Load object's properties using superclass method
        super().load_properties(root)

        # Children list (will be loaded on demand)
        self._children: List[Object] = None

    # ----------------------------------------------------------------------
    # Property   : children
    # Description: Property children getter. Loads children from XML file
    #              on demand.
    # Date       : 12/04/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @property
    def children(self) -> List[Object]:
        """
        Property children getter. Loads children from XML file on demand.
        :return: List of children objects
        """
        # Check if children list is not initialized
        if self._children is None:
            # Initialize children list
            self._children: List[Object] = []

            # Load children from XML file
            self.load_children()

        # Return children list
        return self._children

    # ----------------------------------------------------------------------
    # Method     : load_children
    # Description: It loads the children of a PROTEUS object using an
    #              XML root element <object>.
    # Date       : 13/04/2023
    # Version    : 0.2
    # Author     : Amador Durán Toro
    #              José María Delgado Sánchez
    # ----------------------------------------------------------------------

    def load_children(self) -> None:
        """
        It loads a PROTEUS object's children from an XML root element.
        """

        # Parse and load XML into memory
        root: ET._Element = ET.parse(self.path).getroot()

        # Check root is not None
        assert root is not None, f"Root element is not valid in {self.path}."

        # Load children
        children: ET._Element = root.find(CHILDREN_TAG)

        # If <children> element is not found, ignore children
        if children is None:
            self._children = []
            return

        # Parse object's children
        child: ET._Element
        for child in children:
            child_id: ProteusID = child.attrib[ID_ATTRIBUTE]

            # Check whether the child has an ID
            assert (
                child_id is not None
            ), f"PROTEUS object file {self.id} includes a child without ID."

            # Add the child to the children dictionary and set the parent
            if self.project is not None:
                # If the project is not None, load the child using the project
                object = Object.load(child_id, self.project)
            else:
                # If the project is None, this object is an archetype,
                # so load the child using the object's path
                objects_dir_path: str = os.path.dirname(self.path)
                object_path: str = f"{objects_dir_path}/{child_id}.xml"
                object = Object(object_path)

            object.parent = self

            self.children.append(object)

    # ----------------------------------------------------------------------
    # Method     : get_document
    # Description: It returns the parent document of the object.
    # Date       : 03/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_document(self) -> Object:
        """
        It returns the parent document of the object. It looks recursively
        for the parent until it finds a document object.

        Raises an exception if the document is not found before reaching the
        project root.

        :return: Parent document of the object.
        """

        # Project does not have classes attribute so it will raise an exception
        try:
            if PROTEUS_DOCUMENT in self.classes:
                return self
            else:
                return self.parent.get_document()
        except AttributeError:
            raise Exception(f"Parent document not found for object {self.id}")

    # ----------------------------------------------------------------------
    # Method     : get_descendants
    # Description: It returns a list with all the children of an object.
    # Date       : 23/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_descendants(self) -> List[Object]:
        """
        It returns a list with all the children of an object.
        :return: list with all the children of an object.
        """
        # Return the list with all the descendants of an object
        return self.children

    # ----------------------------------------------------------------------
    # Method     : add_descendant
    # Description: It adds a child to a PROTEUS object.
    # Date       : 26/04/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------

    def add_descendant(self, child: Object, position: int = None) -> None:
        """
        It adds a child to a PROTEUS object if class is accepted.

        :param child: Child Object to be added.
        :param position: Position in the children list where the child will be added.
        """
        # If position is not specified, add the object at the end
        if position is None:
            position = len(self.children)

        # Check if the child is a valid object
        assert isinstance(
            child, Object
        ), f"Child {child} is not a valid PROTEUS object."

        # Check if the child is accepted
        assert self.accept_descendant(
            child=child
        ), f"Child is not accepted by {self.id}.           \
            Accepted children are {self.acceptedChildren}. \
            Child is class {child.classes}.                \
            Accepted parents by child are {child.acceptedParents}."

        # Add the child to the children list and set the parent
        self.children.insert(position, child)
        child.parent = self

        # Set dirty flag
        if self.state != ProteusState.FRESH:
            self.state = ProteusState.DIRTY

        # Add the child id to the project ids
        self.project.ids.add(child.id)

    # ----------------------------------------------------------------------
    # Method     : accept_descendant
    # Description: Checks if a child is accepted by a PROTEUS object.
    # Date       : 03/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------

    def accept_descendant(self, child: Object) -> bool:
        """
        Checks if a child is accepted by a PROTEUS object. Parent must accept
        :Proteus-any and child must accept the object as parent if second level
        object.

        :param child: Child Object to be checked.
        """
        # Check if the child is a valid object
        assert isinstance(
            child, Object
        ), f"Child {child} is not a valid PROTEUS object."

        # Check child is not the same object
        if child.id is self.id:
            return False

        # Check the object branch does not contain the child already
        # as parent
        def get_parents(obj: Object) -> List[ProteusID]:
            parents = []
            if obj.parent is not None and isinstance(obj.parent, Object):
                parents.append(obj.parent.id)
                parents.extend(get_parents(obj.parent))
            return parents

        if child.id in get_parents(self):
            return False

        # --------------------------------------------------------
        # Condition 1 - child accepted parents must be PROTEUS_ANY
        # or contain one of the object class

        accepted_parent_common_classes = [
            c for c in child.acceptedParents if c in self.classes
        ]

        condition_1 = (
            PROTEUS_ANY in child.acceptedParents
            or len(accepted_parent_common_classes) > 0
        )

        # --------------------------------------------------------
        # Condition 2 - self accepted children must be PROTEUS_ANY
        # or contain one of the child class

        accepted_children_common_classes = [
            c for c in self.acceptedChildren if c in child.classes
        ]

        condition_2 = (
            PROTEUS_ANY in self.acceptedChildren
            or len(accepted_children_common_classes) > 0
        )

        # BOTH conditions must be true
        return condition_1 and condition_2

    # ----------------------------------------------------------------------
    # Method     : generate_xml
    # Description: It generates an XML element for the object.
    # Date       : 16/09/2022
    # Version    : 0.2
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------

    def generate_xml(self) -> ET._Element:
        """
        It generates an XML element for the object.
        """
        # Create <object> element and set ID
        object_element = ET.Element(OBJECT_TAG)
        object_element.set(ID_ATTRIBUTE, self.id)
        object_element.set(CLASSES_ATTRIBUTE, " ".join(self.classes))
        object_element.set(ACCEPTED_CHILDREN_ATTRIBUTE, " ".join(self.acceptedChildren))
        object_element.set(ACCEPTED_PARENTS_ATTRIBUTE, " ".join(self.acceptedParents))

        if self.selectedCategory is not None and self.selectedCategory != "":
            object_element.set(SELECTED_CATEGORY_ATTRIBUTE, self.selectedCategory)

        # Create <properties> element
        super().generate_xml_properties(object_element)

        # Create <children> element
        children_element = ET.SubElement(object_element, CHILDREN_TAG)

        if self.numbered:
            children_element.set(NUMBERED_ATTRIBUTE, "true")

        # Create <child> subelements
        for child in self.children:
            child_element = ET.SubElement(children_element, CHILD_TAG)
            child_element.set(ID_ATTRIBUTE, child.id)

        return object_element

    # ----------------------------------------------------------------------
    # Method     : get_traces
    # Description: It returns a list with all the traces properties of an object.
    # Date       : 12/09/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_traces(self) -> List[TraceProperty]:
        """
        It returns a list with all the traces properties of an object.
        :return: list with all the traces properties of an object.
        """
        # Return the list with all the traces properties of an object
        return [
            property
            for property in self.properties.values()
            if isinstance(property, TraceProperty)
        ]

    # ----------------------------------------------------------------------
    # Method     : clone_object
    # Description: It clones an element.
    # Date       : 24/04/2023
    # Version    : 0.4
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def clone_object(
        self, parent: Union[Object, Project], project: Project, position: int = None
    ) -> Object:
        """
        Function that clones an object in a new parent. This function doesn't
        save the object in the system but add it to the parent children so
        it will be saved when we save the project.

        Traces cloning behaviour depends on the object. If an object is cloned
        and it has traces, the traces will be cloned. If the traces are connected
        to objects within the object descendants 'universe', traces will be
        reconnected to the new cloned objects ids. This allows to keep track
        of traces within the object and its descendants.

        Traces that target an object not present in the project will be discarded.

        :param parent: Parent of the new object.
        :param project: Project where the object will be saved.
        :param position: Position in the children list where the child will be added.
        :type parent: Union[Object,Project].
        """
        # Map with the ids of the objects that have been cloned and their new ids
        ids_map: Dict[ProteusID, ProteusID] = dict()

        # Codes map to calculate the biggest code for each prefix
        codes_map: Dict[str, ProteusCode] = self._calculate_biggest_code(project)

        # Clone the object
        cloned_object: Object = self._clone_object(
            parent, project, ids_map, codes_map, position
        )

        # Recalculate traces
        self._recalculate_traces(cloned_object, ids_map, project)

        # Return the cloned object
        return cloned_object

    def _clone_object(
        self,
        parent: Union[Object, Project],
        project: Project,
        ids_map: dict,
        codes_map: dict,
        position: int = None,
    ) -> Object:
        """
        Private function for cloning an object in a new parent.

        :param parent: Parent of the new object.
        :param project: Project where the object will be saved.
        :param position: Position in the children list where the child will be added.
        :param ids_map: Dictionary with the ids of the objects that have been cloned and their new ids.
        :return: Cloned object.
        :rtype: Object
        """

        # ------------------------------------------------------------------

        # Helper function to assign a new id to the object
        def _generate_new_id(project: Project) -> ProteusID:
            """
            Helper function that generates a new id for the object.
            """
            # Generate a new id for the object
            new_id = ProteusID(shortuuid.random(length=12))

            # Check if the new id is already in use
            while new_id in project.ids:
                new_id = ProteusID(shortuuid.random(length=12))

            return ProteusID(new_id)

        # Helper function to handle asset cloning
        def _handle_asset_clone(asset_property: Property) -> None:
            """
            Helper function that handles the asset cloning.
            """
            # Skip if the asset property value is None or empty
            if not asset_property.value:
                return

            # Build the source assets path
            # Check if the cloned object is an archetype based on the project attribute
            source_assets_path: pathlib.Path = None
            if is_archetype:
                # NOTE: If object is an archetype, build the path to the assets
                # folder from its own file path. This is known by archetype
                # repository structure convention
                source_assets_path = (
                    pathlib.Path(self.path).parent.parent / ASSETS_REPOSITORY
                )
            else:
                source_assets_path = (
                    pathlib.Path(self.project.path).parent / ASSETS_REPOSITORY
                )

            assert (
                source_assets_path.exists()
            ), f"Source assets path {source_assets_path} does not exist."

            # Build the target assets path
            target_assets_path = pathlib.Path(project.path).parent / ASSETS_REPOSITORY
            if not target_assets_path.exists():
                target_assets_path.mkdir()

            # Look for the asset files in the source assets path
            asset_file_path: pathlib.Path = source_assets_path / asset_property.value
            assert (
                asset_file_path.exists()
            ), f"Asset file {asset_file_path} does not exist."

            # Name collision are not checked. If the asset file already exists
            # in the target assets path, it will be overwritten.
            target_asset_file_path = target_assets_path / asset_property.value

            # To avoid shutil.copy error, we need to check if the target asset
            # file path is different from the source asset file path.
            if target_asset_file_path != asset_file_path:
                # Copy the asset file to the target assets path
                shutil.copy(asset_file_path, target_asset_file_path)
                log.debug(
                    f"Asset {asset_property.value} copied from {asset_file_path} to {target_asset_file_path}."
                )

        # Helper function to handle codeProperty cloning
        def _handle_code_clone(code_property: CodeProperty) -> CodeProperty:
            """
            Helper function that handles the code cloning.
            """
            new_property: CodeProperty = code_property

            # Get the prefix
            prefix = code_property.value.prefix

            # Check if the prefix is in the code map
            if prefix in codes_map:
                # Get the biggest code for the prefix
                biggest_code = codes_map[prefix]

                # Get the next code
                next_code = biggest_code.next()

                # Update the code map
                codes_map[prefix] = next_code

                # Update the new property
                new_property = code_property.clone(next_code)

            return new_property

        # ------------------------------------------------------------------

        # Check if project is not None
        # NOTE: Project instance type cannot be checked with isinstance
        # due to Project dummy class at the beginning of the file.
        assert (
            project.__class__.__name__ == "Project"
        ), "Parent project must be instance of Project."

        # Check if parent is not None
        assert parent.__class__.__name__ == "Project" or isinstance(
            parent, Object
        ), "Parent must be instance of Object or Project"

        # Check if object is an archetype based on the project property
        is_archetype: bool = self.project is None

        # -------------------------------------------------------
        # Object base clonation
        # -------------------------------------------------------
        # We use standart clone instead of deepcopy to avoid unnecessary copies of project and children
        # This improves performance but It is necessary to manually deepcopy properties
        new_object = copy.copy(self)
        new_object.properties = copy.deepcopy(self.properties)

        # Reset children
        new_object._children = []

        # Set new project and FRESH state
        new_object.project = project
        new_object.state = ProteusState.FRESH

        # Assign a new id that is not in use
        old_id: ProteusID = new_object.id
        new_object.id = _generate_new_id(project)
        ids_map[old_id] = new_object.id

        # Create file path
        project_objects_path = pathlib.Path(project.path).parent / OBJECTS_REPOSITORY
        new_object.path = (project_objects_path / f"{new_object.id}.xml").as_posix()

        # -------------------------------------------------------
        # Handle special properties (Date, Code, FileProperties)
        # -------------------------------------------------------
        for property in new_object.properties.values():
            # Handle FileProperty Assets cloning
            if isinstance(property, FileProperty):
                _handle_asset_clone(property)
            # Set current date to :Proteus-date DateProperty
            elif isinstance(property, DateProperty) and property.name == PROTEUS_DATE:
                current_date = datetime.date.today()
                new_date_property = property.clone(current_date)
                new_object.set_property(new_date_property)
            # Increment :Proteus-code CodeProperty if necessary
            elif isinstance(property, CodeProperty) and property.name == PROTEUS_CODE:
                new_code_property = _handle_code_clone(property)
                new_object.set_property(new_code_property)
            # For existing objects in the project, add the word Copy of in the name
            elif property.name == PROTEUS_NAME and not is_archetype:
                new_name_property = property.clone(f"{_(COPY_OF)} {property.value}")
                new_object.set_property(new_name_property)

        # -------------------------------------------------------
        # Parent children update
        # -------------------------------------------------------
        # Add the new object to the parent children and set the parent
        parent.add_descendant(new_object, position)

        # -------------------------------------------------------
        # Children clone
        # -------------------------------------------------------
        # If the object has children we clone them
        for child in self.get_descendants():
            # Clone the child if not dead
            if child.state != ProteusState.DEAD:
                child._clone_object(
                    parent=new_object,
                    project=project,
                    ids_map=ids_map,
                    codes_map=codes_map,
                    position=len(new_object.children),
                )

        # -------------------------------------------------------
        # Checks and return
        # -------------------------------------------------------
        # Check the new object is valid
        assert isinstance(
            new_object, Object
        ), f"Failed to clone {self.id} with parent {parent.id} in project {project.id}."

        # Return the new object
        return new_object

    def _recalculate_traces(
        self, object: Object, ids_map: dict, project: Project
    ) -> None:
        """
        Recalculate traces of an object and given a map with the ids correlation.
        If a target is not found in the project, the trace will be discarded.
        It works recursively, iterating over the object descendants.

        :param object: Object to recalculate traces.
        :param ids_map: Dictionary with the ids of the objects that have been cloned and their new ids.
        """
        # Iterate over traces
        for trace in self.get_traces():
            # Variable to store possible new targets list
            new_targets: List[ProteusID] = []

            # Iterate over targets
            for target in trace.value:
                # If the target is in the conversion map, add the new id
                if target in ids_map:
                    new_targets.append(ids_map[target])
                # If the target is in the project ids, add the target
                elif target in project.ids:
                    new_targets.append(target)
                # If target not in conversion map or project ids, log error
                else:
                    log.error(
                        f"Unexpected target '{target}' in trace '{trace.name}' during object '{object.id}' trace cloning. Target ProteusID was not found in the project and will be discarded."
                    )

            # If new_targets is different from the original targets, update the trace
            if new_targets != trace.value:
                new_trace: TraceProperty = trace.clone(new_targets)
                object.set_property(new_trace)

        # Iterate over children
        for child in object.children:
            # Recalculate traces
            self._recalculate_traces(child, ids_map, project)

    def _calculate_biggest_code(self, project: Project) -> Dict[str, ProteusCode]:
        """
        Calculates the biggest code for each prefix in the project universe.
        It stores the ProteusCode instances in a dictionary with the prefix as key.
        It works recursively, iterating over the object or project descendants.

        :return: Dictionary with the biggest ProteusCode instances for each prefix.
        :rtype: Dict[str, ProteusCode]
        """

        def _calculate_biggest_code_private(
            element: Union[Project, Object], code_map: Dict[str, ProteusCode]
        ) -> Dict[str, ProteusCode]:
            # Iterate over children
            for child in element.get_descendants():
                if child.state != ProteusState.DEAD:
                    code_map = _calculate_biggest_code_private(child, code_map)

            # Iterate over properties
            for property in element.properties.values():
                if isinstance(property, CodeProperty):
                    # Get the prefix
                    prefix = property.value.prefix

                    # If the prefix is not in the code map, add it
                    if prefix not in code_map:
                        code_map[prefix] = property.value
                    # If the prefix is in the code map, check if the current code is bigger
                    else:
                        if int(property.value.number) > int(code_map[prefix].number):
                            code_map[prefix] = property.value

            return code_map

        # Call the private function
        code_map = dict()
        code_map = _calculate_biggest_code_private(project, code_map)

        return code_map

    # ----------------------------------------------------------------------
    # Method     : save
    # Description: It persist an Object in the system. If the object was
    #              already persisted, it will be updated. If the object was
    #              marked as dead, it will be deleted.
    # Date       : 01/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------

    def save(self) -> None:
        """
        It saves an Object in the system.
        """
        # Save every child
        children = list(self.children)
        for child in children:
            child.save()

        # Persist the object if it is DIRTY or FRESH
        if self.state == ProteusState.DIRTY or self.state == ProteusState.FRESH:
            root = self.generate_xml()

            # Get the elementTree, save it in the project path and set state to clean
            tree = ET.ElementTree(root)
            tree.write(
                self.path, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )
            self.state = ProteusState.CLEAN

        # Delete the object if it is DEAD
        elif self.state == ProteusState.DEAD:
            # Delete itself from the parent children
            self.parent.get_descendants().remove(self)

            # Check if the file exists
            # NOTE: file might not exist if the object was created but not saved
            if os.path.exists(self.path):
                # Delete the file
                os.remove(self.path)
