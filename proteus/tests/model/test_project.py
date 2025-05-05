# ==========================================================================
# File: test_project.py
# Description: pytest file for PROTEUS project class
# Date: 15/10/2022
# Version: 0.2
# Author: José María Delgado Sánchez
#         Pablo Rivera Jiménez
# ==========================================================================
# Update: 12/04/2023 (José María)
# Description:
# - Created tests for different Project methods and lazy load of documents.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import os
import pathlib
import shutil
from typing import List, Generator

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_APP_PATH
from proteus.model import PROJECT_FILE_NAME, OBJECTS_REPOSITORY, PROTEUS_NAME
from proteus.model.abstract_object import ProteusState
from proteus.model.archetype_repository import ArchetypeRepository
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.properties import STRING_PROPERTY_TAG
from proteus.application.configuration.config import Config
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.tests import fixtures
from proteus.tests.fixtures import SampleData

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# NOTE: This is a sample project that is used for testing purposes.
SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project"
ARCHETYPE_REPOSITORY_PATH = PROTEUS_APP_PATH / "profiles/basic/archetypes/"

# --------------------------------------------------------------------------
# Fixtures and helpers
# --------------------------------------------------------------------------


@pytest.fixture
def sample_project() -> Project:
    """
    Fixture that returns a PROTEUS sample project.
    """
    return Project.load(SAMPLE_PROJECT_PATH)


@pytest.fixture
def sample_archetype_project() -> Project:
    """
    Fixture that returns a PROTEUS sample archetype project.
    """
    project_arquetypes: List[Project] = ArchetypeRepository.load_project_archetypes(
        Config().profile_settings.archetypes_directory
    )
    return project_arquetypes[0]


@pytest.fixture
def cloned_project(sample_project: Project) -> Generator[Project, None, None]:
    """
    Fixture that clone a PROTEUS sample project. Then deletes the project.
    """
    # Path to the cloned project
    new_project_dir_name = "cloned_project"
    clone_path = PROTEUS_SAMPLE_PROJECTS_PATH
    cloned_project_path = clone_path / new_project_dir_name

    # Remove cloned project if it exists
    if os.path.exists(cloned_project_path):
        shutil.rmtree(cloned_project_path)

    # Clone project
    new_project = sample_project.clone_project(clone_path, new_project_dir_name)

    yield new_project

    # Remove cloned project
    if os.path.exists(cloned_project_path):
        os.chdir(PROTEUS_SAMPLE_PROJECTS_PATH)
        shutil.rmtree(cloned_project_path)


# --------------------------------------------------------------------------
# Project unit tests
# NOTE: Some methods are not testes with Archetype Projects because they
# are not meant to be used with them.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        SAMPLE_PROJECT_PATH / PROJECT_FILE_NAME,
        ARCHETYPE_REPOSITORY_PATH / "projects" / "basic-project-archetype" / "project.xml",
    ],
)
def test_init(path):
    """
    It tests the init method of the Project class.
    """
    # Create a project using the constructor
    test_project = Project(path)

    # Check type of the project
    assert isinstance(
        test_project, Project
    ), f"Project is not an instance of Project class. It is {type(test_project)}"

    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(path)

    # Compare ET element id with the project id
    assert (
        root.attrib["id"] == test_project.id
    ), f"Project id {test_project.id} is not equal to the id of the root element {root.attrib['id']}"


def test_load():
    """
    It tests the load method of the Project class.
    """

    # Load the project
    test_project = Project.load(SAMPLE_PROJECT_PATH)

    # Check type of the project
    assert isinstance(
        test_project, Project
    ), f"Project is not an instance of Project class. It is {type(test_project)}"

    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(SAMPLE_PROJECT_PATH / PROJECT_FILE_NAME)

    # Compare ET element id with the project id
    assert (
        root.attrib["id"] == test_project.id
    ), f"Project id {test_project.id} is not equal to the id of the root element {root.attrib['id']}"


@pytest.mark.parametrize(
    "test_project",
    [
        pytest.lazy_fixtures("sample_project"),
        pytest.lazy_fixtures("sample_archetype_project"),
    ],
)
def test_documents_lazy_load(test_project: Project):
    """
    Test Project documents property lazy loading
    """
    # Check that documents are not loaded yet checking private
    # variable _documents
    assert (
        test_project._documents == None
    ), "Documents should not be loaded if the 'documents' property is not accessed"

    # Check that documents are loaded when accessing documents
    # property for the first time
    assert (
        type(test_project.documents) == list
    ), f"Documents should have been loaded when accessing 'documents'  \
        property but they are of type {type(test_project.documents)}"
    assert (
        type(test_project._documents) == list
    ), f"Documents private var should have been loaded when accessing  \
        'documents' property but they are of type {type(test_project._documents)}"


@pytest.mark.parametrize(
    "test_project",
    [
        pytest.lazy_fixtures("sample_project"),
        pytest.lazy_fixtures("sample_archetype_project"),
    ],
)
def test_load_documents(test_project: Project):
    """
    Test Project load_documents method
    """
    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(test_project.path)

    # Get documents of the xml file and store them in a list
    documents = root.find("documents")
    documents_list: list = []
    for document in documents:
        documents_list.append(document.attrib["id"])

    # Call method to load documents
    # NOTE: This method could be called when accessing documents
    # for the first time and no documents are loaded yet. However,
    # we are calling it explicitly to test it in case lazy loading
    # fails.
    test_project.load_documents()

    # Check that Object contains all the documents of the xml
    documents_ids = [document.id for document in test_project.documents]
    assert all(
        document in documents_ids for document in documents_list
    ), f"Project does not contain all the documents of the xml file.                        \
        Documents in xml file: {documents_list}                                              \
        Documents in Project: {test_project.documents.keys()}"


def test_generate_xml(sample_project: Project):
    """
    Test Project generate_xml method
    """
    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(sample_project.path)

    # Get xml string from xml file
    expected_xml = ET.tostring(
        root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Generate xml
    xml: ET.Element = sample_project.generate_xml()

    # Get xml string from Object
    actual_xml = ET.tostring(
        xml, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Compare xml strings
    assert (
        expected_xml == actual_xml
    ), f"XML strings are not equal. Expected: {expected_xml} Actual: {actual_xml}"


@pytest.mark.parametrize(
    "test_project",
    [
        pytest.lazy_fixtures("sample_project"),
        pytest.lazy_fixtures("sample_archetype_project"),
    ],
)
def test_clone(test_project: Project):
    """
    Test Project clone method
    """
    # Path to the cloned project
    new_project_dir_name = "cloned_project"
    clone_path = PROTEUS_SAMPLE_PROJECTS_PATH
    cloned_project_path = clone_path / new_project_dir_name

    # Remove cloned project if it exists
    if os.path.exists(cloned_project_path):
        shutil.rmtree(cloned_project_path)

    # Clone project
    new_project = test_project.clone_project(clone_path, new_project_dir_name)

    # Check that the project has been cloned
    assert isinstance(
        new_project, Project
    ), f"Project type is not Project. Type: {type(new_project)}"

    # Compare project id
    assert (
        test_project.id == new_project.id
    ), f"Project id is not equal.               \
        Expected: {test_project.id} Actual: {new_project.id}"

    # Compare project path
    assert (
        cloned_project_path == pathlib.Path(new_project.path).parent.resolve()
    ), f"Project path is not equal.                                                \
        Expected: {cloned_project_path} Actual: {new_project.path}"

    # Clean up cloned project directory
    if os.path.exists(cloned_project_path):
        os.chdir(PROTEUS_SAMPLE_PROJECTS_PATH)
        shutil.rmtree(cloned_project_path)


def test_set_property(sample_project: Project):
    """
    Test Abstract Object set_property method
    """
    # Create property
    (new_property, name, _) = fixtures.create_property(
        STRING_PROPERTY_TAG, PROTEUS_NAME, "general", "Test value"
    )

    # Set property
    sample_project.set_property(new_property)

    # Check that property was set
    assert (
        sample_project.get_property(name) == new_property
    ), f"Property was not set. Expected value: {new_property} \
        Actual value: {sample_project.get_property(name)}"


def test_get_ids(sample_project: Project):
    """
    Test Project get_ids_from_project method
    """
    # Expected ids in sample_project, including the project id
    # Get number of files in the Objects folder
    objects_folder = SAMPLE_PROJECT_PATH / OBJECTS_REPOSITORY
    expected_len = len(os.listdir(objects_folder)) + 1

    # Get ids from project
    ids = sample_project.get_ids()

    # Check that ids are equal
    assert (
        len(ids) == expected_len
    ), f"Ids are not equal. Expected: {expected_len}, Actual: {len(ids)} | {ids}"


def test_save_project(cloned_project: Project):
    """
    Test Project save_project method checking that the project xml file
    is updated after saving the project.
    """
    # Set a new name property value
    (new_property, _, _) = fixtures.create_property(
        STRING_PROPERTY_TAG, PROTEUS_NAME, "general", "Test value"
    )
    cloned_project.set_property(new_property)

    # NOTE: There are unit tests for set_property, generate_xml, clone_project
    # method so we are not checking that the property was set correctly or that
    # the xml was generated correctly.

    # Save project
    cloned_project.save_project()

    # Get xml string from generate xml method
    generated_xml_root = cloned_project.generate_xml()
    generated_xml = ET.tostring(
        generated_xml_root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Get xml string from xml file
    root: ET.Element = fixtures.get_root(cloned_project.path)
    xml_after_save = ET.tostring(
        root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Check that xml strings are equal and project was saved
    assert xml_after_save == generated_xml, f"XML strings are not equal."


def test_save_project_document_edit(cloned_project: Project):
    """
    Test Project save_project method checking that the document was edited
    reading its xml file.
    """
    # Get document by id
    document_id = SampleData.get("document_1")
    document = [d for d in cloned_project.get_descendants() if d.id == document_id][0]

    # Set a new name property value
    (new_property, _, _) = fixtures.create_property(
        STRING_PROPERTY_TAG, PROTEUS_NAME, "general", "Test value"
    )
    document.set_property(new_property)

    # NOTE: There are unit tests for set_property, generate_xml, clone_project
    # method so we are not checking that the property was set correctly or that
    # the xml was generated correctly.

    # Save project
    cloned_project.save_project()

    # Get xml string from generate xml method
    generated_xml_root = document.generate_xml()
    generated_xml = ET.tostring(
        generated_xml_root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Get xml string from xml file
    root: ET.Element = fixtures.get_root(document.path)
    xml_after_save = ET.tostring(
        root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Check that xml strings are equal and project was saved
    assert xml_after_save == generated_xml, f"XML strings are not equal."


def test_save_project_document_delete(cloned_project: Project):
    """
    Test Project save_project method checking that the object file
    is deleted and document is removed from project children dictionary.
    """
    # Get number of documents before delete
    num_documents_before_delete = len(cloned_project.documents)

    # Delete document and its children (mark as DEAD)
    document: Object = cloned_project.documents[0]
    document.state = ProteusState.DEAD

    # Save project
    cloned_project.save_project()

    # Get number of documents after delete
    num_documents_after_delete = len(cloned_project.documents)

    # Check that xml strings are equal and project was saved
    assert not os.path.exists(document.path), f"Document {document.id} was not deleted."

    # Check that number of documents decreased by 1
    assert (
        num_documents_after_delete == num_documents_before_delete - 1
    ), f"Number of documents did not decrease by 1. \
        Expected: {num_documents_before_delete - 1} \
        Actual: {num_documents_after_delete}"


    # TODO: Test add_descendant and accept descendant (not prioritary for project)
