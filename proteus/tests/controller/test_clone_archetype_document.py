# ==========================================================================
# File: test_clone_archetype_document.py
# Description: pytest file for the PROTEUS clone_archetype_document command.
# Date: 29/11/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import PROTEUS_NAME
from proteus.model.abstract_object import ProteusState
from proteus.services.project_service import ProjectService
from proteus.services.archetype_service import ArchetypeService
from proteus.controller.commands.clone_archetype_document import (
    CloneArchetypeDocumentCommand,
)
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project"


@pytest.fixture
def sample_project_service():
    sample_project_service = ProjectService()
    sample_project_service.load_project(SAMPLE_PROJECT_PATH.as_posix())
    return sample_project_service


@pytest.fixture
def sample_archetype_service():
    service = ArchetypeService()
    # Force load of object archetypes
    service.get_document_archetypes()
    return service


# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------
# NOTE: We take a black box approach to test the command outcoming results.
#       Implementation is tricky because undo will mark the document as
#       deleted and will force redo to behave different in the second run.


@pytest.mark.parametrize(
    "index",
    [0],
)
def test_clone_archetype_document_command_redo(
    sample_project_service: ProjectService,
    sample_archetype_service: ArchetypeService,
    index,
):
    """
    Test that the redo method of the CloneArchetypedocumentCommand class works
    as expected.

    Check archetype was cloned in project in the last position.
    Check project, document and object states

    Comparison is done by comparing :Proteus-name property, this depends on
    the sample data used. Test is parametrized to test all the archetypes in
    the repository (currently 3 29/11/2023).

    NOTE: Object clone_object method is tested in object test suite.
    We assume it works as expected.
    """
    # Arrange -------------------------
    parent = sample_project_service.project
    object_archetype = sample_archetype_service.get_document_archetypes()[index]

    # Act -----------------------------
    command = CloneArchetypeDocumentCommand(
        object_archetype.id,
        sample_project_service,
        sample_archetype_service,
    )

    command.redo()

    # Assert --------------------------
    # Check parent state is DIRTY (project was just loaded, will never be FRESH)
    assert (
        parent.state == ProteusState.DIRTY
    ), f"Project state is not DIRTY. State: {parent.state}"

    # Check the last object in parent is equal to the archetype (compare names)
    last_object = parent.get_descendants()[-1]
    assert (
        last_object.get_property(PROTEUS_NAME).value
        == object_archetype.get_property(PROTEUS_NAME).value
    ), f"Last document in parent is not equal to archetype. \
        Last document: {last_object.get_property(PROTEUS_NAME).value}, \
        Archetype: {object_archetype.get_property(PROTEUS_NAME).value}"

    # Check document and its children state is FRESH
    for id in last_object.get_ids():
        assert (
            sample_project_service._get_element_by_id(id).state == ProteusState.FRESH
        ), f"Element {id} state is not FRESH. State: {sample_project_service._get_element_by_id(id).state}"


@pytest.mark.parametrize(
    "index",
    [0],
)
def test_clone_archetype_object_command_undo(
    sample_project_service: ProjectService,
    sample_archetype_service: ArchetypeService,
    index,
):
    """
    Test that the undo method of the CloneArchetypeDocumentCommand class works
    as expected.

    Check the cloned document (last object in parent) is marked as deleted and
    also its children.
    Check project state is previous to clone.

    NOTE: Object clone_object method is tested in object test suite.
    We assume it works as expected.
    """
    # Arrange -------------------------
    parent = sample_project_service.project
    object_archetype = sample_archetype_service.get_document_archetypes()[index]

    # Store parent state before clone
    before_clone_parent_state = parent.state

    # Act -----------------------------
    command = CloneArchetypeDocumentCommand(
        object_archetype.id,
        sample_project_service,
        sample_archetype_service,
    )

    command.redo()
    command.undo()

    # Assert --------------------------
    # Check parent state is previous to clone
    assert (
        parent.state == before_clone_parent_state
    ), f"Project state is not previous to clone. State: {parent.state}"

    # Check the last document in parent (and object children) is marked as deleted
    last_object = parent.get_descendants()[-1]
    for id in last_object.get_ids():
        assert (
            sample_project_service._get_element_by_id(id).state == ProteusState.DEAD
        ), f"Element {id} is not marked as deleted. State: {sample_project_service._get_element_by_id(id).state}"


@pytest.mark.parametrize(
    "index",
    [0],
)
def test_clone_archetype_object_command_redo_after_undo(
    sample_project_service: ProjectService,
    sample_archetype_service: ArchetypeService,
    index,
):
    """
    Test that the redo method of the CloneArchetypeDocumentCommand class works
    as expected after undo was performed. Redo will restore the document and
    children state to FRESH instead cloning again the archetype.

    Check the cloned document is marked as FRESH and also its children.
    Check project state is DIRTY.

    Comparison is done by comparing :Proteus-name property, this depends on
    the sample data used. Test is parametrized to test all the archetypes in
    the repository (currently 3 29/11/2023).

    NOTE: Object clone_object method is tested in object test suite.
    We assume it works as expected.
    """
    # Arrange -------------------------
    parent = sample_project_service.project
    object_archetype = sample_archetype_service.get_document_archetypes()[index]

    # Act -----------------------------
    command = CloneArchetypeDocumentCommand(
        object_archetype.id,
        sample_project_service,
        sample_archetype_service,
    )

    command.redo()
    command.undo()
    command.redo()

    # Assert --------------------------
    # Check parent state is DIRTY (project was just loaded, will never be FRESH)
    assert (
        parent.state == ProteusState.DIRTY
    ), f"Project state is not DIRTY. State: {parent.state}"

    # Check the last object in parent is equal to the archetype (compare names)
    last_object = parent.get_descendants()[-1]
    assert (
        last_object.get_property(PROTEUS_NAME).value
        == object_archetype.get_property(PROTEUS_NAME).value
    ), f"Last document in parent is not equal to archetype. \
        Last document: {last_object.get_property(PROTEUS_NAME).value}, \
        Archetype: {object_archetype.get_property(PROTEUS_NAME).value}"

    # Check document and children state is FRESH
    for id in last_object.get_ids():
        assert (
            sample_project_service._get_element_by_id(id).state == ProteusState.FRESH
        ), f"Element {id} state is not FRESH. State: {sample_project_service._get_element_by_id(id).state}"
