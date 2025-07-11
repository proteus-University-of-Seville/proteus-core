# ==========================================================================
# File: archetype_repository.py
# Description: PROTEUS archetype repository
# Date: 13/04/2023
# Version: 0.3
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
#         José María Delgado Sánchez
# ==========================================================================
# Update: 01/10/2022 (Amador)
# Description:
# - Code review.
# ==========================================================================
# Update: 13/04/2023 (José María)
# Description:
# - ArcheTypeManager refactor to adapt to the new repository structure.
#   Now uses Project and Object clases and its lazy load instead of
#   proxy classes.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from os import listdir
from os.path import join, isdir, isfile
from pathlib import Path
from typing import Dict, List, Set
import shutil

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET
from strenum import StrEnum

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import (
    OBJECTS_REPOSITORY,
    ASSETS_REPOSITORY,
    ID_ATTRIBUTE,
    ProteusClassTag,
)
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.properties import FileProperty

# logging configuration
log = logging.getLogger(__name__)

DOCUMENT_FILE = "document.xml"
OBJECTS_FILE = "objects.xml"
PROJECT_FILE = "project.xml"
GITIGNORE_FILE = ".gitignore"

PROJECT_REPOSITORY_STRUCTURE = [
    OBJECTS_REPOSITORY,
    ASSETS_REPOSITORY,
    PROJECT_FILE,
    GITIGNORE_FILE,
]
DOCUMENT_REPOSITORY_STRUCTURE = [OBJECTS_REPOSITORY, ASSETS_REPOSITORY, DOCUMENT_FILE]
OBJECT_REPOSITORY_STRUCTURE = [OBJECTS_REPOSITORY, ASSETS_REPOSITORY, OBJECTS_FILE]


# --------------------------------------------------------------------------
# Class: ArchetypesType
# Description: String-based enumeration for archetypes' types
# Date: 01/10/2022
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
# https://stackoverflow.com/questions/58608361/string-based-enum-in-python
# --------------------------------------------------------------------------


class ArchetypesType(StrEnum):
    """
    Enumeration for archetypes' types.
    """

    PROJECTS = "projects"
    DOCUMENTS = "documents"
    OBJECTS = "objects"


# --------------------------------------------------------------------------
# Class: ArchetypeRepository
# Description: Class for managing PROTEUS archetypes
# Date: 13/04/2023
# Version: 0.2
# Author: Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ----------------------------------------------------------------------


class ArchetypeRepository:
    """
    An utility class for managing PROTEUS archetypes. It must provide a way
    to get the project, document, and object archetypes on demand from an
    archetype repository.
    """

    # ======================================================================
    # Archetypes loading methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method: load_object_archetypes (static)
    # Description: It load object archetypes
    # Date: 01/09/2023
    # Version: 0.3
    # Author: Pablo Rivera Jiménez
    #         José María Delgado Sánchez
    # ----------------------------------------------------------------------

    @staticmethod
    def load_object_archetypes(
        archetypes_folder: Path,
    ) -> Dict[str, Dict[str, List[Object]]]:
        """
        Method that loads the object archetypes from an archetype repository.
        If no archetype repository is provided, it will use the default one.

        :param archetypes_folder: The path to the archetype repository.

        :return: A dict with key archetype group/category type and value
        dict of object lists by class (its main  class).
        """
        log.info(
            f"ArchetypeRepository - load object archetypes from {archetypes_folder}"
        )
        # Build archetypes directory name from archetype type
        archetypes_dir: str = join(archetypes_folder, ArchetypesType.OBJECTS)

        # Scan all the subdirectories in the archetypes directory (one depth level only)
        # TODO: this means that ALL archetypes must be in one subdirectory, i.e., that
        #       no archetypes are supposed to be in the root directory, AND that only one
        #       level of subdirectories is allowed.
        subdirs: List[str] = [
            f for f in listdir(archetypes_dir) if isdir(join(archetypes_dir, f))
        ]

        # Check there is no files in the root directory
        assert all(
            [not isfile(join(archetypes_dir, f)) for f in listdir(archetypes_dir)]
        ), f"Unexpected files in {archetypes_dir}. Check the object archetypes directory structure."

        # We create a dictionary to store the result
        object_arquetype_dict: Dict[str, Dict] = {}

        # Order the subdirectories by the number in the name
        subdirs.sort(key=lambda x: int(x[:2]))

        # For each subdirectory, containing the archetypes of a given group
        for group_subdir in subdirs:
            # Create dict to store the list of objects of the class
            object_arquetype_by_class: Dict[str, List[Object]] = {}

            # Build the full path to the subdirectory
            object_archetype_class_path: str = join(archetypes_dir, group_subdir)

            # Get object pointer file. Inside we find inside it the ids that
            # referes to the objects and omit the rest of children objects
            objects_pointer_file: str = join(object_archetype_class_path, OBJECTS_FILE)

            # Check project file and objects directory exists
            assert isfile(
                objects_pointer_file
            ), f"Object archetype file {objects_pointer_file} not found."
            assert isdir(
                join(archetypes_dir, group_subdir, OBJECTS_REPOSITORY)
            ), f"Objects directory not found in {join(archetypes_dir, group_subdir)}."

            # Check the arquetype structure is correct
            assert all(
                [
                    (d in OBJECT_REPOSITORY_STRUCTURE)
                    for d in listdir(join(archetypes_dir, group_subdir))
                ]
            ), f"Unexpected files or directories in {join(archetypes_dir, group_subdir)}. Check the archetype directory structure."

            # Parse the XML file
            objects_pointer_xml: ET._ElementTree = ET.parse(objects_pointer_file)
            objects_id_list: list[str] = [
                child.attrib[ID_ATTRIBUTE] for child in objects_pointer_xml.getroot()
            ]

            # For each object id, we create the object and add it to the list
            for object_id in objects_id_list:
                # We get the path of the object
                objects_path = join(object_archetype_class_path, "objects")
                object_path: str = join(objects_path, f"{object_id}.xml")

                # Check the object archetype file exists
                assert isfile(
                    object_path
                ), f"Object archetype file {object_path} not found. Check {OBJECTS_FILE} file."

                # We create the object
                object: Object = Object(object_path)

                # Access the last class of the object
                object_class: ProteusClassTag = object.classes[-1]
                if object_class in object_arquetype_by_class:
                    object_arquetype_by_class[object_class].append(object)
                else:
                    object_arquetype_by_class[object_class] = [object]

            # Parse subdirectory name to get the group name
            # NOTE: objects group directories are named as XX_name_of_the_group
            # where XX is a number. This is done to order the groups. Max number
            # of groups is 99.
            group_subdir_name: str = group_subdir[3:]

            # We add the list to the dictionary
            object_arquetype_dict[group_subdir_name] = object_arquetype_by_class

        return object_arquetype_dict

    # ----------------------------------------------------------------------
    # Method: load_document_archetypes (static)
    # Description: It load document archetypes
    # Date: 13/04/2023
    # Version: 0.2
    # Author: Pablo Rivera Jiménez
    #         José María Delgado Sánchez
    # ----------------------------------------------------------------------

    @staticmethod
    def load_document_archetypes(archetypes_folder: Path) -> list[Object]:
        """
        Method that loads the document archetypes from an archetype repository.
        If no archetype repository is provided, it will use the default one.

        :param archetypes_folder: The path to the archetype repository.

        :return: A list of documents (Objects) objects.
        """
        log.info(
            f"ArchetypeRepository - load document archetypes from {archetypes_folder}"
        )
        # Build archetypes directory name from archetype type
        archetypes_dir: str = join(archetypes_folder, ArchetypesType.DOCUMENTS)

        # Scan all the subdirectories in the archetypes directory (one depth level only)
        # TODO: this means that ALL archetypes must be in one subdirectory, i.e., that
        #       no archetypes are supposed to be in the root directory, AND that only one
        #       level of subdirectories is allowed.
        subdirs: list[str] = [
            f for f in listdir(archetypes_dir) if isdir(join(archetypes_dir, f))
        ]

        # Check there is no files in the root directory
        assert all(
            [not isfile(join(archetypes_dir, f)) for f in listdir(archetypes_dir)]
        ), f"Unexpected files in {archetypes_dir}. Check the document archetypes directory structure."

        document_archetype_list: list[Object] = list()

        # For each document archetype subdir
        for subdir in subdirs:
            # Build the full path to the subdirectory
            archetype_dir_path: str = join(archetypes_dir, subdir)

            # Get document pointer file. Inside we find inside it the id that
            # referes to the main document (the one with class ':Proteus-document')
            document_pointer_file: str = join(archetype_dir_path, DOCUMENT_FILE)

            # Check project file and objects directory exists
            assert isfile(
                document_pointer_file
            ), f"Document archetype file {document_pointer_file} not found."
            assert isdir(
                join(archetypes_dir, subdir, OBJECTS_REPOSITORY)
            ), f"Objects directory not found in {join(archetypes_dir, subdir)}."

            # Check the arquetype structure is correct
            assert all(
                [
                    (d in DOCUMENT_REPOSITORY_STRUCTURE)
                    for d in listdir(join(archetypes_dir, subdir))
                ]
            ), f"Unexpected files or directories in {join(archetypes_dir, subdir)}. Check the archetype directory structure."

            # Parse the XML file
            document_pointer_xml: ET._ElementTree = ET.parse(document_pointer_file)

            # Get the id of the root document from document.xml
            document_id: str = document_pointer_xml.getroot().attrib[ID_ATTRIBUTE]

            # Build the path to the root document
            objects_path = join(archetype_dir_path, "objects")
            document_archetype_file_path = join(objects_path, document_id + ".xml")

            # Check the document archetype file exists
            assert isfile(
                document_archetype_file_path
            ), f"Document archetype file {document_archetype_file_path} not found. Check {DOCUMENT_FILE} file."

            # We create an object from the archetype
            document_archetype: Object = Object(document_archetype_file_path)

            # We add it to the list
            document_archetype_list.append(document_archetype)

        return document_archetype_list

    # ----------------------------------------------------------------------
    # Method: load_project_archetypes (static)
    # Description: It loads project archetypes from archetypes repository
    # Date: 13/04/2023
    # Version: 0.2
    # Author: Pablo Rivera Jiménez
    #         José María Delgado Sánchez
    # ----------------------------------------------------------------------

    @staticmethod
    def load_project_archetypes(archetypes_folder: Path) -> list[Project]:
        """
        Method that loads the project archetypes in a list from an archetype
        repository. If no archetype repository is provided, it will use the
        default one.

        :param archetypes_folder: The path to the archetype repository.

        :return: A list of Project objects.
        """
        log.info(
            f"ArchetypeRepository - load project archetypes from {archetypes_folder}"
        )
        # Build archetypes directory name from archetype type (project)
        archetypes_dir: str = join(archetypes_folder, ArchetypesType.PROJECTS)

        # Scan all the subdirectories in the archetypes directory (one depth level only)
        # TODO: this means that ALL archetypes must be in one subdirectory, i.e., that
        #       no archetypes are supposed to be in the root directory, AND that only one
        #       level of subdirectories is allowed.
        subdirs: list[str] = [
            f for f in listdir(archetypes_dir) if isdir(join(archetypes_dir, f))
        ]

        # Check there is no files in the root directory
        assert all(
            [not isfile(join(archetypes_dir, f)) for f in listdir(archetypes_dir)]
        ), f"Unexpected files in {archetypes_dir}. Check the project archetypes directory structure."

        # Result as a list of Projects
        project_archetype_list: list[Project] = []

        # For each subdirectory
        for subdir in subdirs:
            # Build the full path to the project archetype file
            project_archetype_file_path: str = join(
                archetypes_dir, subdir, PROJECT_FILE
            )

            # Check project file and objects directory exists
            assert isfile(
                project_archetype_file_path
            ), f"Project archetype file {project_archetype_file_path} not found."
            assert isdir(
                join(archetypes_dir, subdir, OBJECTS_REPOSITORY)
            ), f"Objects directory not found in {join(archetypes_dir, subdir)}."

            # Check the arquetype structure is correct
            assert all(
                [
                    (d in PROJECT_REPOSITORY_STRUCTURE)
                    for d in listdir(join(archetypes_dir, subdir))
                ]
            ), f"Unexpected files or directories in {join(archetypes_dir, subdir)}. Check the archetype directory structure."

            # We create a project from the archetype
            project_archetype: Project = Project(project_archetype_file_path)

            # We add it to the result list
            project_archetype_list.append(project_archetype)

        return project_archetype_list

    # ======================================================================
    # Archetypes storing methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method: store_object_archetype (static)
    # Description: It stores an object archetype in the archetype repository
    # Date: 25/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def store_object_archetype(
        archetypes_folder: Path, assets_directoy: Path, archetype: Object, group: str
    ) -> None:
        """
        Method that stores an object as an archetype in the archetype repository.

        :param archetypes_folder: The path to the archetype repository.
        :param assets_directoy: Directory where the assets are stored (if any).
        :param archetype: The object to store as an archetype.
        :param group: The group of the archetype.
        """
        log.info(
            f"ArchetypeRepository - store object archetype '{archetype.id}' in group '{group}'"
        )

        # Get the archetype repository path
        archetypes_dir: Path = archetypes_folder / ArchetypesType.OBJECTS

        # Get the group directory path
        archetype_group_dir: Path = None
        for subdir in archetypes_dir.iterdir():
            subdir_name = subdir.name.lower()
            if group.lower() in subdir_name and subdir.is_dir():
                archetype_group_dir = subdir

        # Check the group directory exists
        assert (
            archetype_group_dir is not None
        ), f"Group directory '{group}' not found in '{archetypes_dir}'"

        # Write in the objects.xml file
        objects_pointer_file: Path = archetype_group_dir / OBJECTS_FILE
        objects_pointer_xml: ET._ElementTree = ET.parse(objects_pointer_file)
        objects_pointer_root: ET.Element = objects_pointer_xml.getroot()
        ET.SubElement(objects_pointer_root, "object", {ID_ATTRIBUTE: archetype.id})
        objects_xml_tree = ET.ElementTree(objects_pointer_root)
        objects_xml_tree.write(
            objects_pointer_file,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        # Get the objects to store and remove DEAD objects
        objects_to_store: Set[Object] = archetype.get_descendants_recursively(ignore_dead_children=True)

        # Store the objects
        for obj in objects_to_store:
            object_xml: ET._Element = obj.generate_xml()
            object_xml_tree = ET.ElementTree(object_xml)
            object_path: Path = (
                archetype_group_dir / OBJECTS_REPOSITORY / f"{obj.id}.xml"
            )
            object_xml_tree.write(
                object_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )

            # Iterate over the properties to store the assets
            for prop in obj.properties.values():
                if isinstance(prop, FileProperty):
                    if prop.value is None or prop.value == "":
                        continue
                    
                    asset_path: Path = assets_directoy / prop.value
                    asset_destination: Path = (
                        archetype_group_dir / ASSETS_REPOSITORY / prop.value
                    )
                    asset_destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(asset_path, asset_destination)

    # ----------------------------------------------------------------------
    # Method: store_document_archetype (static)
    # Description: It stores a document archetype in the archetype repository
    # Date: 29/10/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def store_document_archetype(
        archetypes_folder: Path, assets_directoy: Path, archetype: Object, directory_name: str
    ) -> None:
        """
        Method that stores a document as an archetype in the archetype repository.

        :param archetypes_folder: The path to the archetype repository.
        :param assets_directoy: Directory where the assets are stored (if any).
        :param archetype: The document to store as an archetype.
        :param directory_name: The name of the directory where the archetype will be stored.
        """
        log.info(
            f"ArchetypeRepository - store document archetype '{archetype.id}' in directory '{directory_name}'"
        )

        # Get the archetype repository path
        documents_archetypes_dir: Path = archetypes_folder / ArchetypesType.DOCUMENTS

        # Get the directory path
        archetype_dir: Path = documents_archetypes_dir / directory_name

        # Check it does not exist
        assert not archetype_dir.exists(), f"Directory '{archetype_dir}' already exists"

        # Create the directory
        archetype_dir.mkdir()

        # Create the document.xml file
        document_pointer_file: Path = archetype_dir / DOCUMENT_FILE
        document_pointer_xml: ET._Element = ET.Element("document")
        document_pointer_xml.set(ID_ATTRIBUTE, archetype.id)
        document_pointer_xml_tree = ET.ElementTree(document_pointer_xml)
        document_pointer_xml_tree.write(
            document_pointer_file,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        # Get the objects to store and remove DEAD objects
        objects_to_store: Set[Object] = archetype.get_descendants_recursively()

        # Create the objects directory
        objects_path = archetype_dir / OBJECTS_REPOSITORY
        objects_path.mkdir()

        # Store the objects
        for obj in objects_to_store:
            object_xml: ET._Element = obj.generate_xml()
            object_xml_tree = ET.ElementTree(object_xml)
            object_path: Path = objects_path / f"{obj.id}.xml"
            object_xml_tree.write(
                object_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )

            # Iterate over the properties to store the assets
            for prop in obj.properties.values():
                if isinstance(prop, FileProperty):
                    if prop.value is None or prop.value == "":
                        continue

                    asset_path: Path = assets_directoy / prop.value
                    asset_destination: Path = (
                        archetype_dir / ASSETS_REPOSITORY / prop.value
                    )
                    asset_destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(asset_path, asset_destination)
