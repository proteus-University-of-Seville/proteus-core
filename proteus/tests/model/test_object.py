# ==========================================================================
# File: test_object.py
# Description: pytest file for PROTEUS object class
# Date: 15/10/2022
# Version: 0.2
# Author: José María Delgado Sánchez
#         Pablo Rivera Jiménez
# ==========================================================================
# Update: 12/04/2023 (José María)
# Description:
# - Created tests for different Object methods and lazy load of children.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Union

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import (
    ID_ATTRIBUTE,
    CLASSES_ATTRIBUTE,
    ACCEPTED_CHILDREN_ATTRIBUTE,
    PROTEUS_NAME,
    PROTEUS_ANY,
    ProteusID,
)
from proteus.model.properties import STRING_PROPERTY_TAG
from proteus.model.abstract_object import ProteusState
from proteus.model.object import Object
from proteus.model.project import Project
from proteus.model.archetype_repository import ArchetypeRepository
from proteus.application.configuration.config import Config
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.tests.fixtures import SampleData
from proteus.tests import fixtures

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# NOTE: This is a sample project that is used for testing purposes. The
#       sample object id was selected from this project.
SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project"
SAMPLE_OBJECT_ID = SampleData.get("section_with_dependencies_outside_and_inside")
SAMPLE_DOCUMENT_ID = SampleData.get("document_1")

# --------------------------------------------------------------------------
# Fixtures and helpers
# --------------------------------------------------------------------------


@pytest.fixture
def sample_project() -> Project:
    """
    Fixture that returns a PROTEUS sample project.
    """
    return Project.load(SAMPLE_PROJECT_PATH)


# TODO: For rich tests we need sample archetype objects. This is a temporary
#       based on the current archetype repository content (16/04/2023)
#       solution. Sample archetype objects should have children to test
#       lazy loading and loading of children completely.
@pytest.fixture
def sample_archetype_document() -> Object:
    """
    Fixture that returns a PROTEUS sample archetype document object.
    """
    archetype_list: list[Object] = ArchetypeRepository.load_document_archetypes(
        Config().profile_settings.archetypes_directory
    )
    return archetype_list[0]  # Known archetype document with multiple children


@pytest.fixture
def sample_archetype_object() -> Object:
    """
    Fixture that returns a PROTEUS sample archetype object object.
    """
    archetype_type_dict = ArchetypeRepository.load_object_archetypes(
        Config().profile_settings.archetypes_directory
    )
    # Known archetype type general (00_general directory)
    archetype_class_dict = archetype_type_dict["general"]
    # Known archetype class (section)
    archetype_list = archetype_class_dict["section"]
    return archetype_list[0]


@pytest.fixture
def sample_object(sample_project) -> Object:
    """
    Fixture that returns a PROTEUS sample object.
    """
    return Object.load(SAMPLE_OBJECT_ID, sample_project)


@pytest.fixture
def sample_document(sample_project) -> Object:
    """
    Fixture that returns a PROTEUS sample document.
    """
    return Object.load(SAMPLE_DOCUMENT_ID, sample_project)


# --------------------------------------------------------------------------
# Object unit tests
# NOTE: Some methods are not tested with Archetype Objects because they
# are not meant to be used with them.
# --------------------------------------------------------------------------


def test_init():
    """
    Test Object initialization method
    """
    # Setup test object
    object_file_path = SAMPLE_PROJECT_PATH / "objects" / f"{SAMPLE_OBJECT_ID}.xml"
    test_object: Object = Object(object_file_path)

    # Check type of the object
    assert isinstance(
        test_object, Object
    ), f"Object is not an instance of Object. It is {type(test_object)}"

    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(test_object.path)

    # Compare ET elements with Object elements
    assert (
        root.attrib[ID_ATTRIBUTE] == test_object.id
    ), "Object id is not the same as the root element id."
    assert (
        root.attrib[ACCEPTED_CHILDREN_ATTRIBUTE].split() == test_object.acceptedChildren
    ), "Object acceptedChildren is not the same as the root element acceptedChildren."
    assert (
        root.attrib[CLASSES_ATTRIBUTE].split() == test_object.classes
    ), "Object classes is not the same as the root element classes."


def test_load(sample_project: Project):
    """
    Test Object load method
    """
    # Setup test object
    test_object: Object = Object.load(SAMPLE_OBJECT_ID, sample_project)

    # Check type of the object
    assert isinstance(
        test_object, Object
    ), f"Object is not an instance of Object. It is {type(test_object)}"

    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(test_object.path)

    # Compare ET elements with Object elements
    assert (
        root.attrib[ID_ATTRIBUTE] == test_object.id
    ), "Object id is not the same as the root element id."
    assert (
        root.attrib[ACCEPTED_CHILDREN_ATTRIBUTE].split() == test_object.acceptedChildren
    ), "Object acceptedChildren is not the same as the root element acceptedChildren."
    assert (
        root.attrib[CLASSES_ATTRIBUTE].split() == test_object.classes
    ), "Object classes is not the same as the root element classes."


@pytest.mark.parametrize(
    "test_object",
    [
        pytest.lazy_fixtures("sample_object"),
        pytest.lazy_fixtures("sample_archetype_document"),
    ],
)
def test_children_lazy_load(test_object: Object):
    """
    Test Object children property lazy loading
    """
    # Check that children are not loaded yet checking private
    # variable _children
    assert (
        test_object._children == None  # noqa: E711
    ), "Children should not be loaded if the 'children' property is not accessed"

    # Check that children are loaded when accessing children
    # property for the first time
    assert (
        isinstance(test_object.children, list)
    ), f"Children should have been loaded when accessing 'children'  \
        property but they are of type {type(test_object.children)}"
    assert (
        isinstance(test_object._children, list)
    ), f"Children private var should have been loaded when accessing \
        'Children' property but they are of type {type(test_object._children)}"


@pytest.mark.parametrize(
    "test_object",
    [
        pytest.lazy_fixtures("sample_object"),
        # pytest.lazy_fixtures("sample_archetype_document"),
    ],
)
def test_load_children(test_object: Object, request):
    """
    Test Object load_children method
    """
    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(test_object.path)

    # Get children of the xml file and store them in a list
    children = root.find("children")
    children_list: list = []
    for child in children:
        children_list.append(child.attrib[ID_ATTRIBUTE])

    # Call method to load children
    # NOTE: This method could be called when accessing children
    # for the first time and no children are loaded yet. However,
    # we are calling it explicitly to test it in case lazy loading
    # fails.
    test_object.load_children()

    # Check that Object contains all the children of the xml
    test_object_children_ids = [o.id for o in test_object.children]
    assert all(
        child in test_object_children_ids for child in children_list
    ), f"Object does not contain all the children of the xml file.                 \
        Children in xml file: {children_list}                                       \
        Children in object: {test_object_children_ids}"


def test_generate_xml(sample_object: Object):
    """
    Test Object generate_xml method
    """
    # Get root element of the xml file
    root: ET.Element = fixtures.get_root(sample_object.path)

    # Get xml string from xml file
    expected_xml = ET.tostring(
        root, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Generate xml
    xml: ET.Element = sample_object.generate_xml()

    # Get xml string from Object
    actual_xml = ET.tostring(
        xml, xml_declaration=True, encoding="utf-8", pretty_print=True
    ).decode()

    # Compare xml strings
    assert expected_xml == actual_xml


# TODO: Test clone object      -> object
#                  arch_object -> object
@pytest.mark.parametrize(
    "test_object_to_clone, test_parent",
    [
        (
            pytest.lazy_fixtures("sample_object"),
            pytest.lazy_fixtures("sample_document"),
        ),
        (
            pytest.lazy_fixtures("sample_document"),
            pytest.lazy_fixtures("sample_project"),
        ),
        (
            pytest.lazy_fixtures("sample_archetype_document"),
            pytest.lazy_fixtures("sample_project"),
        ),
        (
            pytest.lazy_fixtures("sample_archetype_object"),
            pytest.lazy_fixtures("sample_document"),
        ),
    ],
)
def test_clone_object(
    test_object_to_clone: Object,
    test_parent: Union[Object, Project],
    sample_project: Project,
):
    """
    Test Object clone_object method
    """
    # Clone object
    new_object = test_object_to_clone.clone_object(test_parent, sample_project)

    # Check that object was cloned
    assert isinstance(
        new_object, Object
    ), f"Object was not cloned. It is of type {type(new_object)}"

    # Check that object is in fresh state
    assert (
        new_object.state == ProteusState.FRESH
    ), f"Object state is not {ProteusState.FRESH} but {new_object.state}"

    # Check the object is in the parent children
    parent_descendants_ids = [o.id for o in test_parent.get_descendants()]
    assert (
        new_object.id in parent_descendants_ids
    ), f"Object {new_object.id} was not found in {parent_descendants_ids}"

    # Check properties are cloned
    assert (
        test_object_to_clone.properties.keys() == new_object.properties.keys()
    ), f"Properties were not cloned. Expected: {test_object_to_clone.properties.keys()} \
        Actual: {new_object.properties.keys()}"

    # Check traces are cloned
    assert (
        test_object_to_clone.get_traces() == new_object.get_traces()
    ), f"Traces were not cloned. Expected: {test_object_to_clone.get_traces()} \
        Actual: {new_object.get_traces()}"

    # Check the children are in the new object
    # NOTE: This will not work if we clone an object into itself
    # however, this is not a valid use case at the moment
    assert (
        test_object_to_clone.get_ids().__len__() == new_object.get_ids().__len__()
    ), f"Object {new_object.id} does not have the same number of children as \
        the original object {test_object_to_clone.id}"


def test_set_property(sample_object: Object):
    """
    Test Abstract Object set_property method
    """
    # Create property
    (new_property, name, _) = fixtures.create_property(
        STRING_PROPERTY_TAG, PROTEUS_NAME, "general", "Test value"
    )

    # Set property
    sample_object.set_property(new_property)

    # Check that property was set
    assert (
        sample_object.get_property(name) == new_property
    ), f"Property was not set. Expected value: {new_property} \
        Actual value: {sample_object.get_property(name)}"


@pytest.mark.parametrize(
    "parent_accepted_children, parent_classes, child_accepted_parents, child_classes, expected_result",
    [
        (PROTEUS_ANY, "a", PROTEUS_ANY, "a", True),  # Accept any
        ("a", "a", PROTEUS_ANY, "a", True),  # Accept only 'a'
        ("a b", "a", PROTEUS_ANY, "a", True),  # Accept 'a' and 'b'
        ("a b", "a", PROTEUS_ANY, "b", True),  # Accept 'a' and 'b', child is 'b'
        (PROTEUS_ANY, "a", "a", "a", True),  # Accept any, child accepts only 'a' parent
        (
            PROTEUS_ANY,
            "a",
            "a",
            "a b",
            True,
        ),  # Accept any, child accepts only 'a' parent
        ("a", "a", "a", "a b", True),  # Accept only 'a', child is 'a' and 'b'
        ("a", "a", PROTEUS_ANY, "b", False),  # Accept only 'a', child is 'b'
        ("a", "a", "a", "b", False),  # Accept only 'a', child is 'b'
        (
            PROTEUS_ANY,
            "a",
            "b",
            "a",
            False,
        ),  # Parent accepts child class but child does not accept parent class
        (
            "a",
            "a",
            "b",
            "a",
            False,
        ),  # Parent accepts child class but child does not accept parent class
    ],
)
def test_accept_descendant(
    mocker,
    sample_object,
    parent_accepted_children,
    parent_classes,
    child_accepted_parents,
    child_classes,
    expected_result,
):
    """
    Test Object accept_descendant method with different scenarios. For parametrization
    simplicity, we use strings separating classes by spaces and parse them to lists
    in the test.

    Class :Proteus-none is not used in parametrization because gives the same result as
    using a dummy ramdom class that differs from the other classes. If it gets special
    treatment in the future (like :Proteus-any) we should add it to the parametrization.
    """
    # Arrange -------------------
    # Create test objects
    mock_parent = sample_object  # TODO: Find a way to use method on mock object to avoid using sample_object
    mock_child = mocker.MagicMock(spec=Object)

    # Create lists of classes and accepted parents
    mock_parent.id = "parent"
    mock_parent.classes = parent_classes.split()
    mock_parent.acceptedChildren = parent_accepted_children.split()
    mock_child.id = "child"
    mock_child.classes = child_classes.split()
    mock_child.acceptedParents = child_accepted_parents.split()

    # Act -----------------------
    result = mock_parent.accept_descendant(mock_child)

    # Assert --------------------
    assert (
        result == expected_result
    ), f"Parent with classes {mock_parent.classes} and accepted children {mock_parent.acceptedChildren} \
        should accept child with classes {mock_child.classes} and accepted parents {mock_child.acceptedParents} \
        but it does not."


def test_get_document(sample_project: Project):
    """
    Test get_document method returns the document where the object is located.

    NOTE: This method cannot use sample_object fixture. get_document method
    depends on the object's parent which is set during parent's children load.
    Since the sample object fixture is loaded isolated from its parent (just needs
    the project). Even if the load is forced, the parent will load its children as
    new objects instances, sample object reference is just stored in the fixture itself.
    """
    # Arrange -------------------

    # Look for the sample object in the project

    def find_object_by_id(
        item: Object = sample_project, object_id: ProteusID = SAMPLE_OBJECT_ID
    ) -> Object:
        
        if item.id == object_id:
            return item

        for descendant in item.get_descendants():
            result = find_object_by_id(descendant, object_id)
            if result:
                return result

        return None

    test_object = find_object_by_id()

    # Act -----------------------
    document = test_object.get_document()

    # Assert --------------------
    assert (
        document.id == SAMPLE_DOCUMENT_ID
    ), f"Object is not in the expected document {SAMPLE_DOCUMENT_ID}. It is in {document.id}"


# NOTE save method is tested with the save_project method in test_project.py

# TODO: Test add_descendant
