# ==========================================================================
# File: test_archetype_repository.py
# Description: pytest file for the PROTEUS ArchetypeRepository
# Date: 20/10/2022
# Version: 0.2
# Author: José María Delgado Sánchez
#         Pablo Rivera Jiménez
# ==========================================================================
# Update: 15/04/2023 (José María)
# Description:
# - Tests adapted to the new ArchetypeRepository logic
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import os
import shutil
from typing import List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.configuration.config import Config
from proteus.model.archetype_repository import (
    ArchetypeRepository,
    DOCUMENT_ARCHETYPE_ATTRIBUTE,
    get_archetype_key,
)
from proteus.model.object import Object
from proteus.model.project import Project

# --------------------------------------------------------------------------
# Fixtures and helpers
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# ArchetypeRepository unit tests
# --------------------------------------------------------------------------


def test_project_archetype():
    # Get the number of projects in archetypes projects
    current_archetype_repository = Config().profile_settings.archetypes_directory
    dir_path = str(current_archetype_repository / "projects")
    number_of_projects: int = len(os.listdir(dir_path))

    # Check if load project function return all the projects
    projects: list[Project] = ArchetypeRepository.load_project_archetypes(
        current_archetype_repository
    )
    assert (
        len(projects) == number_of_projects
    ), f"Number of archetype projects not match with the number of archetype projects in the directory"

    # Check if the projects are Project objects
    for project in projects:
        assert isinstance(
            project, Project
        ), f"Archetype project {project} is not a Project object"


def test_document_archetype():
    # Get the number of documents in archetypes documents, plus the documents
    # of the project archetypes that are not excluded from the document
    # archetypes
    current_archetype_repository = Config().profile_settings.archetypes_directory
    dir_path = current_archetype_repository / "documents"
    number_of_documents = len(os.listdir(dir_path)) if dir_path.is_dir() else 0
    projects_path = current_archetype_repository / "projects"
    for project_dir in projects_path.iterdir():
        root = ET.parse(project_dir / "project.xml").getroot()
        number_of_documents += len(
            [
                d
                for d in root.iter("document")
                if d.get(DOCUMENT_ARCHETYPE_ATTRIBUTE, "true").lower() != "false"
            ]
        )

    # Check if load document function return all the documents
    documents: list[Object] = ArchetypeRepository.load_document_archetypes(
        current_archetype_repository
    )
    assert (
        len(documents) == number_of_documents
    ), f"Number of archetype documents not match with the number of archetype documents in the directory"

    # Check if the documents are Object objects
    for document in documents:
        assert isinstance(
            document, Object
        ), f"Archetype document {document} is not a Object object"


def test_object_archetype():
    # Get the number of objects arquetypes clases
    current_archetype_repository = Config().profile_settings.archetypes_directory
    dir_path = str(current_archetype_repository / "objects")
    archetype_groups = os.listdir(dir_path)

    # Check if load object function return all the classes
    objects: dict[str, dict[str, List[Object]]] = (
        ArchetypeRepository.load_object_archetypes(current_archetype_repository)
    )
    for archetype_group in archetype_groups:

        # Check if the class is in the objects dictionary (parsed to remove order prefix)
        assert (
            archetype_group[3:] in objects.keys()
        ), f"Archetype group {archetype_group} not found in objects"

        # Parse the objects.xml file of the class
        objects_pointer_xml: ET._ElementTree = ET.parse(
            f"{dir_path}/{archetype_group}/objects.xml"
        )

        # Get the number of objects in the objects.xml file ignoring children objects
        objects_id_list: list[str] = [
            child.attrib["id"] for child in objects_pointer_xml.getroot()
        ]
        number_of_objects_expected = len(objects_id_list)

        # Check if the number of objects in the class is correct
        objects_list: list[Object] = []
        for object in objects[archetype_group[3:]].values():
            objects_list.extend(object)

        assert (
            len(objects_list) == number_of_objects_expected
        ), f"Number of objects in group {archetype_group} do not match with the number of objects in the directory"

        # Check if the objects are Object objects
        for object in objects_list:
            assert isinstance(
                object, Object
            ), f"Archetype object {object} is not a Object object"

    # Check if the number of classes in the directory is correct
    assert len(objects.keys()) == len(
        archetype_groups
    ), f"Number of object archetype groups not match with the number of groups in the directory"

    # Check if the objects groups are stored in the correct order
    archetype_groups.sort(key=lambda x: int(x[:2]))
    correct_order = [name[3:] for name in archetype_groups]
    assert (
        list(objects.keys()) == correct_order
    ), f"Object groups are not stored in the correct order"


# --------------------------------------------------------------------------
# Documents of the project archetypes as document archetypes
# --------------------------------------------------------------------------


@pytest.fixture
def archetypes_copy(tmp_path):
    """
    Copy of the archetypes of the current profile (basic), which has the
    same documents as document archetypes and in its project archetypes.
    """
    source = Config().profile_settings.archetypes_directory
    target = tmp_path / "archetypes"
    shutil.copytree(source, target)
    return target


def _exclude_documents(project_file, document_ids):
    """
    Marks the given documents of a project archetype file as not being
    document archetypes.
    """
    tree = ET.parse(project_file)
    for document in tree.getroot().iter("document"):
        if document.get("id") in document_ids:
            document.set(DOCUMENT_ARCHETYPE_ATTRIBUTE, "false")
    tree.write(project_file, xml_declaration=True, encoding="utf-8")


def test_project_documents_are_document_archetypes(archetypes_copy):
    """
    The documents of the project archetypes are loaded after the document
    archetypes, with a key that tells them apart (even if their ids are the
    same as those of document archetypes) and the name of the project
    archetype they come from.
    """
    documents: list[Object] = ArchetypeRepository.load_document_archetypes(
        archetypes_copy
    )
    loose = [d for d in documents if d.archetype_origin is None]
    from_projects = [d for d in documents if d.archetype_origin is not None]

    assert documents == loose + from_projects
    assert len(from_projects) > 0

    keys = [get_archetype_key(d) for d in documents]
    assert len(keys) == len(set(keys)), f"Repeated archetype keys: {keys}"

    for document in loose:
        assert get_archetype_key(document) == document.id

    for document in from_projects:
        project_dir = archetypes_copy / "projects" / get_archetype_key(document).split("/")[0]
        project = Project(str(project_dir / "project.xml"))
        assert get_archetype_key(document) == f"{project_dir.name}/{document.id}"
        assert document.archetype_origin == project.get_property(":Proteus-name").value
        assert document.id in [d.id for d in project.documents]


def test_excluded_project_documents_are_not_document_archetypes(archetypes_copy):
    """
    Documents with documentArchetype="false" in the project file of a project
    archetype are not document archetypes.
    """
    project_dir = next((archetypes_copy / "projects").iterdir())
    document_ids = [
        d.get("id") for d in ET.parse(project_dir / "project.xml").getroot().iter("document")
    ]
    _exclude_documents(project_dir / "project.xml", document_ids)

    keys = [
        get_archetype_key(d)
        for d in ArchetypeRepository.load_document_archetypes(archetypes_copy)
    ]

    assert not any(key.startswith(f"{project_dir.name}/") for key in keys)


def test_documents_excluded_from_archetypes_are_kept_in_new_projects(
    archetypes_copy, tmp_path
):
    """
    A project created from a project archetype keeps the documents excluded
    from the document archetypes, and its project file does not keep the
    attribute.
    """
    project_dir = next((archetypes_copy / "projects").iterdir())
    document_ids = [
        d.get("id") for d in ET.parse(project_dir / "project.xml").getroot().iter("document")
    ]
    _exclude_documents(project_dir / "project.xml", document_ids)

    archetype = Project(str(project_dir / "project.xml"))
    (tmp_path / "projects").mkdir()
    new_project = archetype.clone_project(str(tmp_path / "projects"), "new_project")

    assert [d.id for d in new_project.documents] == document_ids
    project_file = (tmp_path / "projects" / "new_project" / "proteus.xml").read_text(encoding="utf-8")
    assert DOCUMENT_ARCHETYPE_ATTRIBUTE not in project_file


def test_clones_of_project_document_archetypes_are_not_archetypes(
    archetypes_copy, tmp_path
):
    """
    A document created from a document of a project archetype is a normal
    document: new id, same content, and no archetype key or origin.
    """
    # The largest document of a project archetype (the sample document of the
    # basic profile, which has figures)
    document = max(
        (
            d
            for d in ArchetypeRepository.load_document_archetypes(archetypes_copy)
            if d.archetype_origin is not None
        ),
        key=lambda d: len(d.get_descendants_recursively()),
    )
    # Target project: a copy of another project archetype, so that the assets
    # of the document must be copied from the project archetype it comes from
    source_dir = get_archetype_key(document).split("/")[0]
    target_dir = next(
        p for p in (archetypes_copy / "projects").iterdir() if p.name != source_dir
    )
    archetype = Project(str(target_dir / "project.xml"))
    (tmp_path / "projects").mkdir()
    project = archetype.clone_project(str(tmp_path / "projects"), "target")

    new_document = document.clone_object(project, project)

    assert new_document.id != document.id
    assert new_document.archetype_key is None
    assert new_document.archetype_origin is None
    assert (
        new_document.get_property(":Proteus-name").value
        == document.get_property(":Proteus-name").value
    )
    assert len(new_document.get_descendants_recursively()) == len(
        document.get_descendants_recursively()
    )

    # The assets of the document are copied to the target project
    from proteus.model.properties import FileProperty

    assets = [
        prop.value
        for obj in [new_document, *new_document.get_descendants_recursively()]
        for prop in obj.properties.values()
        if isinstance(prop, FileProperty) and prop.value
    ]
    assert assets, "The sample document has no assets to check"
    for asset in assets:
        assert (tmp_path / "projects" / "target" / "assets" / asset).exists(), asset


def test_profile_without_document_archetypes_directory(archetypes_copy):
    """
    The document archetypes directory is optional: without it, the documents
    of the project archetypes are the document archetypes.
    """
    documents_dir = archetypes_copy / "documents"
    if documents_dir.exists():
        shutil.rmtree(documents_dir)

    documents = ArchetypeRepository.load_document_archetypes(archetypes_copy)

    assert documents
    assert all(d.archetype_origin is not None for d in documents)
