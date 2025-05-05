# ==========================================================================
# File: test_achetype_service.py
# Description: pytest file for the PROTEUS archetype service
# Date: 02/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List, Dict, Union

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.archetype_repository import ArchetypeRepository
from proteus.services.archetype_service import ArchetypeService


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def archetype_service():
    """
    It returns a new instance of the ArchetypeService class.
    """
    return ArchetypeService()


# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------


# test_project_archetypes_lazy_load ----------------------------------------
def test_project_archetypes_lazy_load(archetype_service: ArchetypeService):
    """
    It tests the lazy load of the project archetypes.

    Depends on the archetypes folder content.
    """
    # Arrange -------------------------
    # Check that the project archetypes are not loaded
    assert (
        archetype_service._project_archetypes is None
    ), "_project_archetypes instance attribute should be None"

    # Act -----------------------------
    # Load the project archetypes calling the property
    project_archetypes: List[Project] = archetype_service.get_project_archetypes()

    # Assert --------------------------
    # Check that the project archetypes are loaded
    assert isinstance(
        project_archetypes, list
    ), f"project_archetypes should be a list, not {type(project_archetypes)}"
    assert (
        archetype_service._project_archetypes == project_archetypes
    ), "_project_archetypes should be equal to ArchetypeService.project_archetypes"


# test_document_archetypes_lazy_load ---------------------------------------
def test_document_archetypes_lazy_load(archetype_service: ArchetypeService):
    """
    It tests the lazy load of the document archetypes.

    Depends on the archetypes folder content.
    """
    # Check that the document archetypes are not loaded
    # Arrange -------------------------
    assert (
        archetype_service._document_archetypes is None
    ), "._document_archetypes instance attribute should be None"

    # Act -----------------------------
    # Load the document archetypes calling the property
    document_archetypes: List[Object] = archetype_service.get_document_archetypes()

    # Assert --------------------------
    # Check that the document archetypes are loaded
    assert isinstance(
        document_archetypes, list
    ), f"document_archetypes should be a list, not {type(document_archetypes)}"
    assert (
        archetype_service._document_archetypes == document_archetypes
    ), "_document_archetypes should be equal to ArchetypeService.document_archetypes"


# test_object_arquetypes_lazy_load -----------------------------------------
def test_object_arquetypes_lazy_load(archetype_service: ArchetypeService):
    """
    It tests the lazy load of the object archetypes.

    Depends on the archetypes folder content.
    """
    # Arrange -------------------------
    # Check that the object archetypes are not loaded
    assert (
        archetype_service._object_archetypes is None
    ), "_object_archetypes instance attribute should be None"

    # Act -----------------------------
    # Load the object archetypes calling the property
    object_archetypes: Dict[
        str, List[Object]
    ] = archetype_service.get_object_archetypes()

    # Assert --------------------------
    # Check that the object archetypes are loaded
    assert isinstance(
        object_archetypes, dict
    ), f"object_archetypes should be a dict, not {type(object_archetypes)}"
    assert (
        archetype_service._object_archetypes == object_archetypes
    ), "_object_archetypes should be equal to ArchetypeService.object_archetypes"


# test_archetype_index_load ------------------------------------------------
def test_archetype_index_load(archetype_service: ArchetypeService):
    """
    It tests the lazy load of the archetype index.

    Depends on the archetypes folder content.
    """
    # Arrange | Act -------------------
    # Load the archetypes calling the properties
    project_archetypes: List[Project] = archetype_service.get_project_archetypes()
    document_archetypes: List[Object] = archetype_service.get_document_archetypes()
    object_archetypes: Dict[
        str, Dict[str, List[Object]]
    ] = archetype_service.get_object_archetypes()

    # Get ids of the archetypes
    project_archetypes_ids: List[ProteusID] = set(
        project.id for project in project_archetypes
    )
    document_archetypes_ids: List[ProteusID] = set(
        document.id for document in document_archetypes
    )
    object_archetypes_ids: List[ProteusID] = set()
    for archetype_class_dict in object_archetypes.values():
        for archetype_list in archetype_class_dict.values():
            object_archetypes_ids = object_archetypes_ids.union(
                set(object.id for object in archetype_list)
            )

    archetypes_ids = project_archetypes_ids.union(document_archetypes_ids).union(
        object_archetypes_ids
    )

    # Get the keys from the archetype_index
    archetype_index_keys: List[ProteusID] = set(
        archetype_service.archetype_index.keys()
    )

    # Assert --------------------------
    # Check that the archetype_index is updated
    assert (
        archetypes_ids == archetype_index_keys
    ), "archetype_index should contain the all archetypes"


# test_get_archetype_by_id -------------------------------------------------
@pytest.mark.parametrize(
    "id", ["paragraph", "BASIC", "empty-doc"]
)
def test_get_archetype_by_id(id: str, archetype_service: ArchetypeService):
    """
    It tests the get_archetype_by_id method.

    Depends on the archetypes folder content.
    """
    # Arrange -------------------------
    ARCHETYPE_ID = ProteusID(id)

    # Lazy load the archetypes
    archetype_service.get_project_archetypes()
    archetype_service.get_document_archetypes()
    archetype_service.get_object_archetypes()

    # Act -----------------------------
    # Load the archetype by id
    archetype: Union[Project, Object] = archetype_service._get_archetype_by_id(
        ARCHETYPE_ID
    )

    # Assert --------------------------
    # Check that the archetype is loaded
    assert isinstance(
        archetype, (Project, Object)
    ), f"ArchetypeService.object_archetypes should be a dict, not {type(archetype)}"


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


# test_get_project_archetypes ----------------------------------------------
def test_get_project_archetypes(mocker, archetype_service: ArchetypeService):
    """
    It tests the get_project_archetypes method.
    """
    # Arrange -------------------------
    # Mock ArchetypeRepository.load_project_archetypes static method
    mock_project = mocker.MagicMock(spec=Project)
    mock_project.id = "mock_project_1"

    mock_project_archetypes = [mock_project]
    mocker.patch.object(
        ArchetypeRepository,
        "load_project_archetypes",
        return_value=mock_project_archetypes,
    )

    # Act -----------------------------
    # Load the project archetypes list
    project_archetypes: List[Project] = archetype_service.get_project_archetypes()

    # Assert --------------------------
    # Check that the project archetypes are loaded
    assert isinstance(
        project_archetypes, list
    ), f"project_archetypes should be a list, not {type(project_archetypes)}"

    # Check that ArchetypeRepository.load_project_archetypes static method is called
    ArchetypeRepository.load_project_archetypes.assert_called_once()


def test_get_project_archetypes_invalid_archetypes(
    mocker, archetype_service: ArchetypeService
):
    """
    Test that an assertion error is raised when the archetypes are not a list.
    """
    # Arrange -------------------------
    # Mock the load_project_archetypes function to return an invalid value (not a list)
    mock_archetypes = "invalid archetypes"
    mocker.patch.object(
        ArchetypeRepository, "load_project_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when the archetypes are not a list
    with pytest.raises(AssertionError):
        archetype_service.get_project_archetypes()


def test_get_project_archetypes_duplicate_id(
    mocker, archetype_service: ArchetypeService
):
    # Arrange -------------------------
    # Mock the load_project_archetypes function to return a list with duplicate project IDs
    project_mock = mocker.Mock(spec=Project)
    project_mock.id = "1"
    mock_archetypes = [project_mock, project_mock]
    mocker.patch.object(
        ArchetypeRepository, "load_project_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when duplicate project IDs are found
    with pytest.raises(AssertionError):
        archetype_service.get_project_archetypes()


# test_get_document_archetypes ---------------------------------------------
def test_get_document_archetypes(mocker, archetype_service: ArchetypeService):
    """
    It tests the get_document_archetypes method.
    """
    # Arrange -------------------------
    # Mock ArchetypeRepository.load_document_archetypes static method
    mock_document = mocker.MagicMock(spec=Object)
    mock_document.id = "mock_document_1"

    mock_document_archetypes = [mock_document]

    mocker.patch.object(
        ArchetypeRepository,
        "load_document_archetypes",
        return_value=mock_document_archetypes,
    )

    # Act -----------------------------
    # Load the document archetypes list
    document_archetypes: List[Object] = archetype_service.get_document_archetypes()

    # Assert --------------------------
    # Check that the document archetypes are loaded
    assert isinstance(
        document_archetypes, list
    ), f"document_archetypes should be a list, not {type(document_archetypes)}"

    # Check that ArchetypeRepository.load_document_archetypes static method is called
    ArchetypeRepository.load_document_archetypes.assert_called_once()


def test_get_document_archetypes_invalid_archetypes(
    mocker, archetype_service: ArchetypeService
):
    """
    Test that an assertion error is raised when the archetypes are not a list.
    """
    # Arrange -------------------------
    # Mock the load_document_archetypes function to return an invalid value (not a list)
    mock_archetypes = "invalid archetypes"
    mocker.patch.object(
        ArchetypeRepository, "load_document_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when the archetypes are not a list
    with pytest.raises(AssertionError):
        archetype_service.get_document_archetypes()


def test_get_document_archetypes_duplicate_id(
    mocker, archetype_service: ArchetypeService
):
    """
    Test that an assertion error is raised when there are documents with duplicate IDs.
    """
    # Arrange -------------------------
    # Mock the load_document_archetypes function to return a list with duplicate documentIDs
    document_mock = mocker.Mock(spec=Object)
    document_mock.id = "1"
    mock_archetypes = [document_mock, document_mock]
    mocker.patch.object(
        ArchetypeRepository, "load_document_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when duplicate document IDs are found
    with pytest.raises(AssertionError):
        archetype_service.get_document_archetypes()


# test_get_object_archetypes -----------------------------------------------
def test_get_object_archetypes_groups(mocker, archetype_service: ArchetypeService):
    """
    It tests the get_object_archetypes_groups method.
    """
    # Arrange -------------------------
    mock_object = mocker.MagicMock(spec=Object)
    mock_object.id = "mock_object_1"

    mock_object_archetypes = {"mock_type_1": {"mock_object_class_1": [mock_object]}}
    mocker.patch.object(
        ArchetypeRepository,
        "load_object_archetypes",
        return_value=mock_object_archetypes,
    )

    # Act -----------------------------
    # Load the object archetypes types list
    object_archetypes_groups: List[str] = archetype_service.get_object_archetypes_groups()

    # Assert --------------------------
    # Check that the object archetypes are loaded
    assert isinstance(
        object_archetypes_groups, list
    ), f"object_archetypes should be a list, not {type(object_archetypes_groups)}"

    # Check that ArchetypeRepository.load_object_archetypes static method is called
    ArchetypeRepository.load_object_archetypes.assert_called_once()


def test_get_object_archetypes_by_group(mocker, archetype_service: ArchetypeService):
    """
    It tests the get_object_archetypes_by_group method.
    """
    # Arrange -------------------------
    OBJECT_GROUP = "mock_type_1"
    OBJECT_CLASS = "mock_object_class_1"
    mock_object = mocker.MagicMock(spec=Object)
    mock_object.id = "mock_object_1"

    mock_object_archetypes = {OBJECT_GROUP: {OBJECT_CLASS: [mock_object]}}
    mocker.patch.object(
        ArchetypeRepository,
        "load_object_archetypes",
        return_value=mock_object_archetypes,
    )

    # Act -----------------------------
    # Load the object archetypes list
    object_archetypes_by_class: Dict[
        str, List[Object]
    ] = archetype_service.get_object_archetypes_by_group(OBJECT_GROUP)

    # Assert --------------------------
    # Check that the object archetypes are loaded
    assert isinstance(
        object_archetypes_by_class, dict
    ), f"object_archetypes should be a list, not {type(object_archetypes_by_class)}"

    # Check that ArchetypeRepository.load_object_archetypes static method is called
    ArchetypeRepository.load_object_archetypes.assert_called_once()


def test_get_object_archetypes_invalid_archetypes(
    mocker, archetype_service: ArchetypeService
):
    """
    Test that an assertion error is raised when the archetypes are not a dict.
    """
    # Arrange -------------------------
    # Mock the load_object_archetypes function to return an invalid value (not a dict)
    mock_archetypes = "invalid archetypes"
    mocker.patch.object(
        ArchetypeRepository, "load_object_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when the archetypes are not a dict
    with pytest.raises(AssertionError):
        archetype_service.get_object_archetypes()


def test_get_object_archetypes_duplicate_id(
    mocker, archetype_service: ArchetypeService
):
    """
    Test that an assertion error is raised when there are objects with duplicate IDs.
    """
    # Arrange -------------------------
    # Mock the load_object_archetypes function to return a list with duplicate object IDs
    object_mock = mocker.Mock(spec=Object)
    object_mock.id = "1"
    mock_archetypes = {"General": { "section": [object_mock, object_mock]}}
    mocker.patch.object(
        ArchetypeRepository, "load_object_archetypes", return_value=mock_archetypes
    )

    # Act & Assert --------------------
    # Check that an assertion error is raised when duplicate object IDs are found
    with pytest.raises(AssertionError):
        archetype_service.get_object_archetypes()


# test_get_archetype_by_id -------------------------------------------------
@pytest.mark.parametrize("id", ["", None, "non-existent-id"])
def test_get_archetype_by_id_negative(id: str, archetype_service: ArchetypeService):
    """
    Tests archetype_service._get_archetype_by_id with negative cases. Check that
    it raises the assert exception.
    """
    # Arrange -------------------------
    ARCHETYPE_ID = ProteusID(id)

    # Act | Assert --------------------
    with pytest.raises(AssertionError):
        archetype_service._get_archetype_by_id(ARCHETYPE_ID)


# test_create_project ------------------------------------------------------
@pytest.mark.parametrize(
    "archetype_id, project_name, save_path",
    [("archetype_id_1", "project_name_1", "/path/to/save_1")],
)
def test_create_project(
    mocker, archetype_id, project_name, save_path, archetype_service: ArchetypeService
):
    """
    Test the create_project method. Positive case. Test that the _get_archetype_by_id
    and clone_project methods are called once with the correct parameters.
    """
    # Arrange -------------------------
    # Mock the _get_archetype_by_id method of ArchetypeService
    # return a mock project
    mock_project = mocker.Mock(spec=Project)
    mocker.patch.object(
        archetype_service, "_get_archetype_by_id", return_value=mock_project
    )
    # Mock the clone_project method of the mock project to do nothing
    mocker.patch.object(mock_project, "clone_project", return_value=None)

    # Act -----------------------------
    # Call the create_project method
    archetype_service.create_project(archetype_id, project_name, save_path)

    # Assert --------------------------
    # Assert that _get_archetype_by_id and mock_project.clone_project are called
    # once with the correct parameters
    archetype_service._get_archetype_by_id.assert_called_once_with(archetype_id)
    mock_project.clone_project.assert_called_once_with(save_path, project_name)


@pytest.mark.parametrize(
    "project_name, archetype_type",
    [
        ("", Project),  # Empty project name
        (None, Project),  # None project name
        ("Valid name", Object),  # Invalid archetype type
        ("Valid name", None),  # None archetype type
        (None, None),  # Invalid parameters
    ],
)
def test_create_project_negative(
    mocker, project_name, archetype_type, archetype_service: ArchetypeService
):
    """
    Test the create_project method. Negative case. Test that assert is raised
    when passing incorrect parameters.
    """
    # Arrange -------------------------
    # Mock the _get_archetype_by_id method so we can
    mock_project = mocker.Mock(spec=archetype_type)
    mocker.patch.object(
        archetype_service, "_get_archetype_by_id", return_value=mock_project
    )
    archetype_id: str = "archetype_id_dummy"
    save_path: str = "/path/to/save/dummy"

    # Act | Assert --------------------
    # Call the create_project method
    with pytest.raises(AssertionError):
        archetype_service.create_project(archetype_id, project_name, save_path)


# test_create_object -------------------------------------------------------
@pytest.mark.parametrize(
    "archetype_id, parent, project",
    [("dummy_id", "dummy_parent", "dummy_project")],
)
def test_create_object(
    mocker, archetype_id, parent, project, archetype_service: ArchetypeService
):
    """
    Test the create_object method. Positive case. Test that the _get_archetype_by_id
    and clone_project methods are called once with the correct parameters.
    """
    # Arrange -------------------------
    # Mock the _get_archetype_by_id method of ArchetypeService
    # return a mock object
    mock_object = mocker.Mock(spec=Object)
    mocker.patch.object(
        archetype_service, "_get_archetype_by_id", return_value=mock_object
    )
    # Mock the clone_object method of the mock project to do nothing
    mocker.patch.object(mock_object, "clone_object", return_value=None)

    # Act -----------------------------
    # Call the create_project method
    archetype_service.create_object(archetype_id, parent, project)

    # Assert --------------------------
    # Assert that _get_archetype_by_id and mock_project.clone_project are called
    # once with the correct parameters
    archetype_service._get_archetype_by_id.assert_called_once_with(archetype_id)
    mock_object.clone_object.assert_called_once_with(parent, project)


@pytest.mark.parametrize(
    "archetype_type",
    [(Project), (None)],
)
def test_create_object_negative(
    mocker, archetype_type, archetype_service: ArchetypeService
):
    """
    Test the create_object method. Negative case. Test that assert is raised
    when passing incorrect parameters.
    """
    # Arrange -------------------------
    # Mock the _get_archetype_by_id method so we can
    mock_object = mocker.Mock(spec=archetype_type)
    mocker.patch.object(
        archetype_service, "_get_archetype_by_id", return_value=mock_object
    )
    archetype_id: str = "archetype_id_dummy"
    parent: str = "parent_dummy"
    project: str = "project_dummy"

    # Act | Assert --------------------
    # Call the create_project method
    with pytest.raises(AssertionError):
        archetype_service.create_object(archetype_id, parent, project)
