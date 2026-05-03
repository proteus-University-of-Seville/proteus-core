# ==========================================================================
# File: test_project_service.py
# Description: pytest file for the PROTEUS project service
# Date: 07/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List, Dict

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
from pytest_lazy_fixtures import lf
from lxml import etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_ANY, PROTEUS_DOCUMENT
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.abstract_object import ProteusState
from proteus.model.properties import Property, TraceProperty
from proteus.services.project_service import ProjectService
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.tests.fixtures import SampleData

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project"
EXAMPLE_XML_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project_example_doc.xml"
SAMPLE_OBJECT_ID = SampleData.get("section_dl_2")
SAMPLE_DOCUMENT_ID = SampleData.get("document_1")

# Render test data
ONE_DOC_PROJECT = "one_doc_project"
RENDER_DOCUMENT_ID = SampleData.get("document_to_render", ONE_DOC_PROJECT)


@pytest.fixture
def project_service():
    """
    It returns a new instance of the ProjectService class. The project is
    loaded from the SAMPLE_PROJECT_PATH.

    Depends on Project.load method.
    """
    project_service: ProjectService = ProjectService()
    project_service.load_project(SAMPLE_PROJECT_PATH.as_posix())
    return project_service


@pytest.fixture
def basic_project_service():
    """
    It returns a new instance of the ProjectService class. There is no project
    loaded.
    """
    project_service: ProjectService = ProjectService()
    return project_service


@pytest.fixture
def mock_property(mocker):
    """
    It returns a mock property.
    """
    return mocker.MagicMock(spec=Property)


@pytest.fixture
def mock_trace(mocker):
    """
    It returns a mock trace.
    """
    return mocker.MagicMock(spec=TraceProperty)

# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------


def test_load_project(project_service: ProjectService):
    """
    It tests the initialization of the project service. check that the project
    is the correct class and that the project index is initialized.

    NOTE: load_project method is called in the project_service fixture.
    """
    # Assert --------------------------
    # Check that the project service is initialized
    assert isinstance(
        project_service.project, Project
    ), "Project should be instance of Project"

    # Get all ids from the project
    project_ids: List[ProteusID] = project_service.project.get_ids()

    # Get ids present in the index
    index_ids: List[ProteusID] = project_service.project_index.keys()

    # Get project traced objects ids
    def get_traced_ids(object: Object):
        traced_ids = set()
        for trace in object.get_traces():
            traced_ids.update(set(trace.value))
        for child in object.get_descendants():
            traced_ids.update(get_traced_ids(child))
        return traced_ids

    traced_ids = set()
    for object in project_service.project.get_descendants():
        traced_ids.update(get_traced_ids(object))

    # Check that all ids are present in the index
    assert set(index_ids) == set(project_ids), (
        f"Some ids are not present in the index"
        f"\n\tProject ids: {project_ids}"
        f"\n\tIndex ids: {index_ids}"
    )

    # Check that the traces index was populated with the correct traced ids
    assert set(project_service.traces_index.keys()) == traced_ids, (
        f"Traces index should not be empty"
        f"\n\tTraces index: {project_service.traces_index}"
    )


def test_get_project_structure(project_service: ProjectService):
    """
    It tests the get_project_structure method.
    """
    # Arrange -------------------------
    # Get project documents ids
    project_document_ids: List[Object] = project_service.project.documents

    # Act -----------------------------
    # Get project structure
    project_structure: List[Object] = project_service.get_project_structure()

    # Assert --------------------------
    # Check that the project structure is correct
    assert set(project_document_ids) == set(project_structure), (
        f"Project structure is not correct"
        f"\n\tProject structure: {project_structure}"
        f"\n\tProject service structure: {project_service.project_structure}"
    )


def test_get_object_structure(project_service: ProjectService):
    """
    It tests the get_object_structure method.
    """
    # Act -----------------------------
    # Get object structure
    object_structure: Dict[Object, List] = project_service.get_object_structure(
        SAMPLE_OBJECT_ID
    )

    # Post-actions --------------------
    # Get object
    object: Object = list(object_structure.keys())[0]
    # Get object children
    object_children: List[Object] = set(object.children)
    # Get object structure children ids
    children_dicts: List[Dict] = object_structure[object]
    object_structure_children: List[ProteusID] = set(
        [list(d.keys())[0] for d in children_dicts]
    )

    # Assert --------------------------
    # TODO: Check structure in all depth levels
    # Check that the object structure has 1 element in first depth level
    assert (
        len(object_structure.keys()) == 1
    ), f"Object structure should have 1 element in first depth level"

    # Check that the object structure is correct second depth level
    assert object_children == object_structure_children, (
        f"Object structure is not correct"
        f"\n\tObject children: {object_children}"
        f"\n\tObject structure children: {object_structure_children}"
    )


# test generate_project_xml ------------------------------------------------------
def test_generate_project_xml(
    basic_project_service: ProjectService,
):
    """
    Test the generate_project_xml method.
    """
    # Arrange -------------------------
    project_path: str = (PROTEUS_SAMPLE_PROJECTS_PATH / ONE_DOC_PROJECT).as_posix()
    basic_project_service.load_project(project_path)

    # Create parser
    # NOTE: CDATA is not stripped because it is needed for the comparison.
    parser = ET.XMLParser(remove_blank_text=True, strip_cdata=False)
    # Get the example document xml
    example_xml: ET._Element = ET.parse(EXAMPLE_XML_PATH, parser=parser).getroot()
    example_xml_string: bytes = ET.tostring(
        example_xml, xml_declaration=False, encoding="unicode", pretty_print=False
    )

    # Act -----------------------------
    project_xml: ET._Element = basic_project_service.generate_project_xml()
    project_xml_string: bytes = ET.tostring(
        project_xml, xml_declaration=False, encoding="unicode", pretty_print=False
    )


    # Assert --------------------------
    assert project_xml_string == example_xml_string, (
        f"The generated xml is different from the example xml, check {EXAMPLE_XML_PATH}"
        f"\n\nGenerated xml: {project_xml_string}"
        f"\n\nExample xml: {example_xml_string}"
    )



@pytest.mark.parametrize(
    "object_name, expected_traced_objects, expected_sources_for_each_object",
    [
        ("target_with_2_sources_1", 1, 2),
        ("target_with_2_sources_2", 1, 2),
        ("section_with_2_children_targeted", 2, 2),
    ],
)
def test_get_traces_dependencies(
    project_service: ProjectService,
    object_name,
    expected_traced_objects,
    expected_sources_for_each_object,
):
    """
    Tests get_traces_dependencies method. Uses example project data
    to check different scenarios.

    NOTE: For easier testing, data is fixed so every traced object
    will have same number of sources (object pointing to them).

    TODO: Find a way to test more complex scenarios.
    """
    # Arrange -------------------------
    object_id = SampleData.get(object_name)

    # Act -----------------------------
    traced_objects = project_service.get_traces_dependencies(object_id)

    # Assert --------------------------
    # Check is a dict
    assert isinstance(
        traced_objects, dict
    ), f"Traced objects should be a dict but it is {type(traced_objects)}"

    # Check number of traced objects
    assert (
        len(traced_objects.keys()) == expected_traced_objects
    ), f"Traced objects should be {expected_traced_objects} but it is {len(traced_objects.keys())}"

    # Check number of sources for each traced object
    for traced_object in traced_objects.values():
        assert (
            len(traced_object) == expected_sources_for_each_object
        ), f"Traced object should have {expected_sources_for_each_object} sources but it has {len(traced_object)}"


@pytest.mark.parametrize(
    "object_name, expected_traced_objects, expected_sources_for_each_object",
    [
        ("target_with_2_sources_1", 1, 2),
        ("target_with_2_sources_2", 1, 2),
        ("section_with_2_children_targeted", 2, 1),
    ],
)
def test_get_traces_dependencies(
    project_service: ProjectService,
    object_name,
    expected_traced_objects,
    expected_sources_for_each_object,
):
    """
    Tests get_traces_dependencies_outside method. Uses example project data
    to check different scenarios.

    NOTE: For easier testing, data is fixed so every traced object
    will have same number of sources (object pointing to them).

    TODO: Find a way to test more complex scenarios.
    """
    # Arrange -------------------------
    object_id = SampleData.get(object_name)

    # Act -----------------------------
    traced_objects = project_service.get_traces_dependencies_outside(object_id)

    # Assert --------------------------
    # Check is a dict
    assert isinstance(
        traced_objects, dict
    ), f"Traced objects should be a dict but it is {type(traced_objects)}"

    # Check number of traced objects
    assert (
        len(traced_objects.keys()) == expected_traced_objects
    ), f"Traced objects should be {expected_traced_objects} but it is {len(traced_objects.keys())}"

    # Check number of sources for each traced object
    for traced_object in traced_objects.values():
        assert (
            len(traced_object) == expected_sources_for_each_object
        ), f"Traced object should have {expected_sources_for_each_object} sources but it has {len(traced_object)}"


@pytest.mark.parametrize(
    "object_name, new_parent_name, new_position, expected_current_position",
    [
        ("simple_paragraph", "document_1", 2, 0),
        ("simple_paragraph", "document_1", 3, 0),
        ("simple_paragraph", "document_1", 8, 0),  # Move to the last position
        ("simple_objective", "document_1", 0, 6),  # Move to the first position
    ],
)
def test_change_object_position_same_parent(
    project_service: ProjectService,
    object_name: str,
    new_parent_name: str,
    new_position: int,
    expected_current_position: int,
):
    """
    NOTE: DEAD objects are pushed to the end of the list to calculate the
    position relative to non-DEAD objects.
    """
    # Arrange -------------------------
    # Object
    object_id = SampleData.get(object_name)
    object = project_service._get_element_by_id(object_id)
    old_parent = object.parent
    old_parent_descendants = [
        o for o in old_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    current_position = old_parent_descendants.index(object)

    # Check test data is correct
    assert (
        current_position == expected_current_position
    ), f"Test data is not correct. Current position is {current_position} and expected {expected_current_position}"

    # New parent
    new_parent_id = SampleData.get(new_parent_name)
    new_parent = project_service._get_element_by_id(new_parent_id)

    # Act -----------------------------
    project_service.change_object_position(object_id, new_parent_id, new_position)

    # Assert --------------------------
    # Check object appears in the new parent
    new_parent_descendants_updated = [
        o for o in new_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    assert (
        object in new_parent_descendants_updated
    ), f"Object {object.id} should be in parent {new_parent.id} but it was not found."

    # Calculate expected position. If new_position is greater than the current position, we must decrease it by 1
    # to compensate the fact that the 'old' object is removed from the parent after being inserted.
    expected_position = new_position
    if new_position > current_position:
        expected_position = new_position - 1

    assert (
        new_parent_descendants_updated.index(object) == expected_position
    ), f"Object {object.id} should be in position {expected_position} in parent {new_parent.id} but it is in position \
        {new_parent_descendants_updated.index(object)}"

    # Check both parents are the same
    assert (
        object.parent == new_parent == old_parent
    ), f"Object {object.id} parent {object.parent.id} should be equal to new parent {new_parent.id} and old parent {old_parent.id}"

    # Check parent state is DIRTY
    assert (
        old_parent.state == ProteusState.DIRTY
        and new_parent.state == ProteusState.DIRTY
    ), f"Old parent state should be DIRTY, but it is {old_parent.state}"


@pytest.mark.parametrize(
    "object_name, new_parent_name, new_position, expected_current_position",
    [
        (
            "simple_paragraph",
            "section_dl_1",
            0,
            0,
        ),
        (
            "simple_paragraph",
            "section_dl_1",
            1,
            0,
        ),
    ],
)
def test_change_object_position_different_parent(
    project_service: ProjectService,
    object_name: str,
    new_parent_name: str,
    new_position: int,
    expected_current_position: int,
):
    """
    NOTE: DEAD objects are pushed to the end of the list to calculate the
    position relative to non-DEAD objects.
    """
    # Arrange -------------------------
    # Object
    object_id = SampleData.get(object_name)
    object = project_service._get_element_by_id(object_id)
    old_parent = object.parent
    old_parent_descendants = [
        o for o in old_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    current_position = old_parent_descendants.index(object)

    # Check test data is correct
    assert (
        current_position == expected_current_position
    ), f"Test data is not correct. Current position is {current_position} and expected {expected_current_position}"

    # New parent
    new_parent_id = SampleData.get(new_parent_name)
    new_parent = project_service._get_element_by_id(new_parent_id)

    # Act -----------------------------
    project_service.change_object_position(object_id, new_parent_id, new_position)

    # Assert --------------------------
    # Check object appears in the new parent
    new_parent_descendants_updated = [
        o for o in new_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    assert (
        object in new_parent_descendants_updated
    ), f"Object {object.id} should be in parent {new_parent.id} but it was not found."

    # Check the object is in the new position
    assert (
        new_parent_descendants_updated.index(object) == new_position
    ), f"Object {object.id} should be in position {new_position} in parent {new_parent.id} but it is in position \
        {new_parent_descendants_updated.index(object)}"

    # Check the new parent is the correct
    assert (
        object.parent == new_parent and object.parent != old_parent
    ), f"Object {object.id} parent {object.parent.id} should be equal to new parent {new_parent.id} and different from old parent {old_parent.id}"

    # Check old and new parent state are DIRTY
    assert (
        old_parent.state == ProteusState.DIRTY
    ), f"Old parent state should be DIRTY, but it is {old_parent.state}"

    assert (
        new_parent.state == ProteusState.DIRTY
    ), f"New parent state should be DIRTY, but it is {new_parent.state}"

    # Check that the object is not in the old parent
    assert (
        object not in old_parent.get_descendants()
    ), f"Object {object.id} should not be in old parent {old_parent.id} but it was found."


@pytest.mark.parametrize(
    "object_name, new_parent_name, new_position, expected_current_position",
    [
        (
            "simple_paragraph",
            "section_dl_1",
            None,
            0,
        ),
    ],
)
def test_change_object_position_different_parent_none(
    project_service: ProjectService,
    object_name: str,
    new_parent_name: str,
    new_position: int,
    expected_current_position: int,
):
    """
    NOTE: DEAD objects are pushed to the end of the list to calculate the
    position relative to non-DEAD objects.
    """
    # Arrange -------------------------
    # Object
    object_id = SampleData.get(object_name)
    object = project_service._get_element_by_id(object_id)
    old_parent = object.parent
    old_parent_descendants = [
        o for o in old_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    current_position = old_parent_descendants.index(object)

    # Check test data is correct
    assert (
        current_position == expected_current_position
    ), f"Test data is not correct. Current position is {current_position} and expected {expected_current_position}"

    # New parent
    new_parent_id = SampleData.get(new_parent_name)
    new_parent = project_service._get_element_by_id(new_parent_id)

    # Act -----------------------------
    project_service.change_object_position(object_id, new_parent_id, new_position)

    # Assert --------------------------
    # Check object appears in the new parent
    new_parent_descendants_updated = [
        o for o in new_parent.get_descendants().copy() if o.state != ProteusState.DEAD
    ]
    assert (
        object in new_parent_descendants_updated
    ), f"Object {object.id} should be in parent {new_parent.id} but it was not found."

    # Check the object is in the new position (last position)
    last_position = len(new_parent_descendants_updated) - 1
    assert (
        new_parent_descendants_updated.index(object) == last_position
    ), f"Object {object.id} should be in position {last_position} in parent {new_parent.id} but it is in position \
        {new_parent_descendants_updated.index(object)}"

    # Check the new parent is the correct
    assert (
        object.parent == new_parent and object.parent != old_parent
    ), f"Object {object.id} parent {object.parent.id} should be equal to new parent {new_parent.id} and different from old parent {old_parent.id}"

    # Check old and new parent state are DIRTY
    assert (
        old_parent.state == ProteusState.DIRTY
    ), f"Old parent state should be DIRTY, but it is {old_parent.state}"

    assert (
        new_parent.state == ProteusState.DIRTY
    ), f"New parent state should be DIRTY, but it is {new_parent.state}"

    # Check that the object is not in the old parent
    assert (
        object not in old_parent.get_descendants()
    ), f"Object {object.id} should not be in old parent {old_parent.id} but it was found."


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


# test_update_properties ---------------------------------------------------
def test_update_properties(mocker, basic_project_service: ProjectService):
    """
    Test the update_properties method.
    """
    # Arrange -------------------------
    # Mock the _get_element_by_id method
    mock_element = mocker.MagicMock(spec=Object)
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", return_value=mock_element
    )
    mocker.patch.object(mock_element, "set_property", return_value=None)

    mock_property = mocker.MagicMock(spec=Property)

    # Act -----------------------------
    basic_project_service.update_properties("id", [mock_property, mock_property])

    # Assert --------------------------
    assert (
        mock_element.set_property.call_count == 2
    ), f"set_property should be called twice"

    assert (
        basic_project_service._get_element_by_id.call_count == 1
    ), f"_get_element_by_id should be called once"


@pytest.mark.parametrize(
    "property_list",
    [
        (None),
        ("invalid list"),
        ([1, 2, 3]),
        (lf("mock_property")),
        ([None, lf("mock_property")]),
        ([lf("mock_property"), 1, 2, 3]),
    ],
)
def test_update_properties_negative(
    mocker,
    property_list,
    basic_project_service: ProjectService,
):
    """
    Test the update_properties method with invalid properties parameters.
    """
    # Arrange -------------------------
    # Mock the _get_element_by_id method
    mock_element = mocker.MagicMock(spec=Object)
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", return_value=mock_element
    )
    mocker.patch.object(mock_element, "set_property", return_value=None)

    # Act | Assert --------------------
    with pytest.raises(AssertionError):
        basic_project_service.update_properties("id", property_list)

    # Check that the _get_element_by_id method is not called
    assert (
        basic_project_service._get_element_by_id.call_count == 0
    ), f"_get_element_by_id should not be called"

    # Check that the set_property method is not called
    assert (
        mock_element.set_property.call_count == 0
    ), f"set_property should not be called"



def test_update_traces_properties_discard_one_invalid_target(mocker, basic_project_service: ProjectService, mock_trace: TraceProperty):
    """
    Test the update_traces method with one trace that has invalid targets, only the valid target should be added.
    """

    # Arrange -------------------------
    # Mock _load_traces_index method
    mocker.patch.object(basic_project_service, "_load_traces_index", return_value=None)

    # Valid target object
    valid_target_mock: Object = mocker.MagicMock(spec=Object)
    valid_target_mock.id = "valid_target_id"
    valid_target_mock.state = ProteusState.CLEAN
    valid_target_mock.classes = ["mock_class"]

    # Invalid target object
    invalid_target_mock: Object = mocker.MagicMock(spec=Object)
    invalid_target_mock.id = "invalid_target_id"
    invalid_target_mock.state = ProteusState.DEAD
    invalid_target_mock.classes = ["mock_class"]

    # Create object
    mock_element: Object = mocker.MagicMock(spec=Object)
    mock_element.id = "element_id"
    mock_element.state = ProteusState.CLEAN
    mock_element.classes = ["mock_class"]
    mocker.patch.object(mock_element, "set_property", return_value=None)

    # Mock the _get_element_by_id method
    def get_element_by_id_side_effect(id):
        if id == "element_id":
            return mock_element
        elif id == "valid_target_id":
            return valid_target_mock
        elif id == "invalid_target_id":
            return invalid_target_mock
        else:
            return None
        
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", side_effect=get_element_by_id_side_effect
    )

    # Mock load_traces_index method
    mocker.patch.object(basic_project_service, "_load_traces_index", return_value=None)

    # Set valid and invalid targets
    mock_trace.name = "mock_trace_name"
    mock_trace.value = ["valid_target_id", "invalid_target_id"]

    mock_element.properties = {mock_trace.name: mock_trace}

    # Copy mock_trace
    mock_trace_clone: TraceProperty = mocker.MagicMock(spec=TraceProperty)
    mock_trace_clone.name = "mock_trace_name"
    mock_trace_clone.value = ["valid_target_id"]

    mocker.patch.object(mock_trace, "clone", return_value=mock_trace_clone)

    # Act -----------------------------
    basic_project_service.update_properties("element_id", [mock_trace])

    # Assert --------------------------

    # Check that the trace is added to the object
    # Since trace is cloned, we check the name
    assert (
        "mock_trace_name" in mock_element.properties
    ), f"Trace should be added to the object"

    # Check that the clone method was called with just valid target
    mock_trace.clone.assert_called_once_with(new_targets=["valid_target_id"])

    # Check that the set_property method was called with the cloned trace
    mock_element.set_property.assert_called_once_with(mock_trace_clone)

    # Check that load_traces_index is called
    assert (
        basic_project_service._load_traces_index.call_count == 1
    ), f"_load_traces_index should be called once"

    # Element state is not checked since it is set_property responsibility to update it

@pytest.mark.parametrize(
    "trace_list",
    [
        (None),
        ("invalid list"),
        ([1, 2, 3]),
        (lf("mock_trace")),
        ([None, lf("mock_trace")]),
        ([lf("mock_trace"), 1, 2, 3]),
    ],
)
def test_update_traces_negative_invalid_elements_in_traces_list(
    mocker,
    trace_list: List[TraceProperty],
    basic_project_service: ProjectService,
):
    """
    Test the update_traces method with invalid traces parameters.
    """
    # Arrange -------------------------
    mocker.patch.object(basic_project_service, "_get_element_by_id", return_value=None)

    # Act | Assert --------------------
    with pytest.raises(AssertionError):
        basic_project_service.update_properties("id", trace_list)

    # Check that the _get_element_by_id method is not called
    assert (
        basic_project_service._get_element_by_id.call_count == 0
    ), f"_get_element_by_id should not be called"


def test_update_traces_negative_document_trace(
    mocker,
    basic_project_service: ProjectService,
    mock_trace: TraceProperty,
):
    """
    Test the update_traces method with invalid traces parameters. The traces
    contains a document.
    """
    # Arrange -------------------------
    # A document tracing itself
    mock_element: Object = mocker.MagicMock(spec=Object)
    mock_element.properties = {}
    mock_element.state = ProteusState.CLEAN
    mock_element.classes = [PROTEUS_DOCUMENT]
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", return_value=mock_element
    )

    mocker.patch.object(basic_project_service, "_load_traces_index", return_value=None)

    mock_trace.value = ["id"]
    trace_list = [mock_trace]

    # Act -----------------------------
    basic_project_service.update_properties("id", trace_list)


    # Assert --------------------------
    # Check mock_element properties are empty
    assert (
        len(mock_element.properties) == 0
    ), f"Object properties should be empty but it is {mock_element.properties}"

    # load_traces_index should not be called
    assert (
        basic_project_service._load_traces_index.call_count == 0
    ), f"_load_traces_index should not be called"

    # Element state should remain CLEAN
    assert (
        mock_element.state == ProteusState.CLEAN
    ), f"Object state should be CLEAN but it is {mock_element.state}"


def test_update_traces_negative_dead_object(
    mocker,
    basic_project_service: ProjectService,
    mock_trace: TraceProperty,
):
    """
    Test the update_traces method with invalid traces parameters. The traces
    contains a dead object.
    """
    # Arrange -------------------------
    # A document tracing itself
    mock_element: Object = mocker.MagicMock(spec=Object)
    mock_element.properties = {}
    mock_element.state = ProteusState.DEAD
    mock_element.classes = ["mock_class"]
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", return_value=mock_element
    )

    mocker.patch.object(basic_project_service, "_load_traces_index", return_value=None)

    mock_trace.value = ["id"]
    trace_list = [mock_trace]

    # Act -----------------------------
    basic_project_service.update_properties("id", trace_list)


    # Assert --------------------------
    # Check mock_element properties are empty
    assert (
        len(mock_element.properties) == 0
    ), f"Object properties should be empty but it is {mock_element.properties}"

    # load_traces_index should not be called
    assert (
        basic_project_service._load_traces_index.call_count == 0
    ), f"_load_traces_index should not be called"

    # Cannot check CLEAN state because the element is tracing itself and it is a dead object
    # Anyways, if _load_traces_index is not called, the state should remain the same. It is
    # tested in previous tests.


def test_update_traces_negative_self_tracing(
    mocker,
    basic_project_service: ProjectService,
    mock_trace: TraceProperty,
):
    """
    Test the update_traces method with invalid traces parameters. The traces
    contains a dead object.
    """
    # Arrange -------------------------
    # A document tracing itself
    mock_element: Object = mocker.MagicMock(spec=Object)
    mock_element.id = "id"
    mock_element.properties = {}
    mock_element.state = ProteusState.CLEAN
    mock_element.classes = ["mock_class"]
    mocker.patch.object(
        basic_project_service, "_get_element_by_id", return_value=mock_element
    )

    mocker.patch.object(basic_project_service, "_load_traces_index", return_value=None)

    mock_trace.value = ["id"]
    trace_list = [mock_trace]

    # Act -----------------------------
    basic_project_service.update_properties("id", trace_list)


    # Assert --------------------------
    # Check mock_element traces are empty
    assert (
        len(mock_element.properties) == 0
    ), f"Object traces should be empty but it is {mock_element.properties}"

    # load_traces_index should not be called
    assert (
        basic_project_service._load_traces_index.call_count == 0
    ), f"_load_traces_index should not be called"

    # Element state should remain CLEAN
    assert (
        mock_element.state == ProteusState.CLEAN
    ), f"Object state should be CLEAN but it is {mock_element.state}"



# test_get_element_by_id ---------------------------------------------------
def test_get_element_by_id(
    mocker,
    basic_project_service: ProjectService,
):
    """
    Test the _get_element_by_id method.
    """
    # Arrange -------------------------
    # Insert mock object in the index
    mock_object = mocker.MagicMock(spec=Object)
    basic_project_service.project_index = {"id": mock_object}
    mocker.patch.object(basic_project_service, "_populate_index", return_value=None)

    # Act -----------------------------
    element = basic_project_service._get_element_by_id("id")

    # Assert --------------------------
    # Check that the element is the mock object
    assert element == mock_object, f"Element should be {mock_object}"

    # Check that _populate_index is not called
    assert (
        basic_project_service._populate_index.call_count == 0
    ), f"_populate_index should not be called"


def test_get_element_by_id_negative(
    mocker,
    basic_project_service: ProjectService,
):
    """
    Test the _get_element_by_id method asserting and populating the index
    when the element is not in the index.
    """
    # Arrange -------------------------
    # Mock the _populate_index method
    mocker.patch.object(basic_project_service, "_populate_index", return_value=None)

    # Act | Assert --------------------
    with pytest.raises(AssertionError):
        element = basic_project_service._get_element_by_id("id")

    # Check that _populate_index is called
    assert (
        basic_project_service._populate_index.call_count == 1
    ), f"_populate_index should be called once"


@pytest.mark.parametrize(
    "selected_classes",
    [
        (["a"]),
        (["a", "b"]),
        (["b", "c"]),
        (["a", "b", "c", "d"]),
        (["d"]),
    ],
)
@pytest.mark.parametrize(
    "classes_1, classes2, classes_3",
    [
        ("a", "b", "c"),
        ("a b", "a", "a c"),
        ("a b c", "b", "a"),
    ],
)
def test_get_objects(
    mocker, basic_project_service, selected_classes, classes_1, classes2, classes_3
):
    """
    Test get_objects method with different selected classes. Classes for dummy objects are
    passed as strings and converted to lists in the test for simplicity.

    Do not tests :Proteus-any/empty classes or death objects
    """
    # Arrange -------------------------
    # Mock the project_index.values()
    project_index = {}
    for index, classes in enumerate([classes_1, classes2, classes_3]):
        mock_object = mocker.MagicMock(spec=Object)
        mock_object.classes = classes.split()
        mock_object.state = ProteusState.CLEAN
        project_index[index] = mock_object

    basic_project_service.project_index = project_index

    # Calculate expected objects
    # In the original method selected classes are iterated for each object
    # because there are much more objects than selected classes. In this test
    # is done differently to simplify the test.
    expected_objects = set()
    for c in selected_classes:
        for o in project_index.values():
            if c in o.classes:
                expected_objects.add(o)

    # Act -----------------------------
    objects = basic_project_service.get_objects(selected_classes)

    # Assert --------------------------
    # Check that the objects are the expected
    assert (
        set(objects) == expected_objects
    ), f"Expected {len(expected_objects)} objects but got {len(objects)}."


@pytest.mark.parametrize(
    "selected_classes",
    [
        ([PROTEUS_ANY]),
        (None),
        ([]),
        (["a", PROTEUS_ANY]),
    ],
)
@pytest.mark.parametrize(
    "classes_1, classes2, classes_3",
    [
        ("a", "b", "c"),
        ("a b", "a", "a c"),
        ("a b c", "b", "a"),
    ],
)
def test_get_objects_any(
    mocker, basic_project_service, selected_classes, classes_1, classes2, classes_3
):
    """
    Test get_objects method where all objects are expected to be returned.
    """
    # Arrange -------------------------
    # Mock the project_index.values()
    project_index = {}
    for index, classes in enumerate([classes_1, classes2, classes_3]):
        mock_object = mocker.MagicMock(spec=Object)
        mock_object.classes = classes.split()
        mock_object.state = ProteusState.CLEAN
        project_index[index] = mock_object

    basic_project_service.project_index = project_index

    # Act -----------------------------
    objects = basic_project_service.get_objects(selected_classes)

    # Assert --------------------------
    assert set(objects) == set(
        project_index.values()
    ), f"Expected {len(project_index.values())} objects but got {len(objects)}."


# NOTE: test save_project might not be necessary because it is a simple call
# to the project save method, which is tested in the project model tests.
