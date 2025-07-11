# ==========================================================================
# File: test_delete_object.py
# Description: pytest file for the PROTEUS delete object command
# Date: 27/11/2023
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

from proteus.model import ProteusID
from proteus.model.properties import TraceProperty
from proteus.model.abstract_object import ProteusState
from proteus.services.project_service import ProjectService
from proteus.application.state.manager import StateManager
from proteus.controller.commands.delete_object import DeleteObjectCommand
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.tests.fixtures import SampleData

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project"


@pytest.fixture
def sample_project_service():
    sample_project_service = ProjectService()
    sample_project_service.load_project(SAMPLE_PROJECT_PATH.as_posix())
    return sample_project_service


# --------------------------------------------------------------------------
# Integration tests
# --------------------------------------------------------------------------
# NOTE: We take a black box approach to test the command outcoming results
#       since implementation is complex due to traces dependencies.


@pytest.mark.parametrize(
    "object_name",
    [
        ("simple_paragraph"),
        ("section_dl_1"),
        ("section_dl_2"),
        ("target_with_2_sources_1"),
        ("section_with_2_children_targeted"),
    ],
)
def test_delete_object_command_redo(
    sample_project_service: ProjectService,
    object_name,
):
    """
    Test that the redo method of the DeleteObjectCommand class works as
    expected.

    Check object and children are marked as DEAD and parent as DIRTY.
    Check sources are marked as DIRTY.
    Check sources specific traces have been updated (less targets than before).
    Check object is deselected.
    Do not check events are emitted.

    Parametrized with multiple objects to test different children depths and
    traces dependencies.
    """
    # Arrange -------------------------
    object_id = SampleData.get(object_name)

    # Store ids of the object and its children to check their state later
    object = sample_project_service._get_element_by_id(object_id)
    object_and_children_ids = object.get_ids()

    # Find objects that are tracing the object or its children (sources)
    sources_ids = set()
    for target_id, sources in sample_project_service.traces_index.items():
        for source_id, _ in sources:
            # Add sources that point the object or its children but exclude
            # the object and its children themselves
            if (
                source_id not in object_and_children_ids
                and target_id in object_and_children_ids
            ):
                sources_ids.add(source_id)

    # Store a copy of sources traces before the command execution
    # Just copy the traces that are tracing the object or its children
    sources_traces_before: Dict[ProteusID, Dict[ProteusID, TraceProperty]] = {}
    for source_id in sources_ids:
        source_dict: Dict[ProteusID, TraceProperty] = {}
        source = sample_project_service._get_element_by_id(source_id)
        for trace in source.get_traces():
            # Check if the trace is tracing the object or its children
            common_ids = [id for id in trace.value if id in object_and_children_ids]
            if len(common_ids) > 0:
                source_dict[trace.name] = trace
        sources_traces_before[source_id] = source_dict

    # Act -----------------------------
    delete_object_command = DeleteObjectCommand(object_id, sample_project_service)

    delete_object_command.redo()

    # Assert --------------------------
    # Check all states are DEAD
    assert all(
        [
            sample_project_service._get_element_by_id(id).state == ProteusState.DEAD
            for id in object_and_children_ids
        ]
    ), "All objects states must be DEAD"

    # Check parent state is DIRTY
    assert (
        object.parent.state == ProteusState.DIRTY
    ), f"Parent object state must be DIRTY but it is {object.parent.state}"

    # Check sources states are DIRTY
    assert all(
        [
            sample_project_service._get_element_by_id(id).state == ProteusState.DIRTY
            for id in sources_ids
        ]
    ), "All sources states must be DIRTY"

    # Check sources traces have been updated
    for source_id, traces in sources_traces_before.items():
        for trace_name, trace in traces.items():
            # Get source trace
            source = sample_project_service._get_element_by_id(source_id)
            source_updated_trace = source.get_property(trace_name)
            assert len(source_updated_trace.value) < len(
                trace.value
            ), f"Updated trace {trace_name} of source {source_id} must have less targets than before \
                (before: {len(trace.value)}, after: {len(source_updated_trace.value)}) \
                Current targets: {source_updated_trace.value} \
                Previous targets: {trace.value}\
                Ids: {object_and_children_ids}"

    # Check deselect object has been called
    assert (
        StateManager().get_current_object() is None
    ), f"Current object must be None but it is {StateManager().current_object}"


@pytest.mark.parametrize(
    "object_name",
    [
        ("simple_paragraph"),
        ("section_dl_1"),
        ("section_dl_2"),
        ("target_with_2_sources_1"),
        ("section_with_2_children_targeted"),
    ],
)
def test_delete_object_command_undo(
    sample_project_service: ProjectService,
    object_name,
):
    """
    Test that the undo method of the DeleteObjectCommand class works as
    expected.

    Check object, children and parent are restored to their previous state.
    Check sources are restored to their previous state.
    Check sources specific traces have been restored.
    Do not check events are emitted.

    Parametrized with multiple objects to test different children depths and
    traces dependencies.

    NOTE: This test is not independent from redo function. If redo does not
    work as expected, this test will not provide useful output. Check redo
    test output to ensure this test is working properly.
    """
    # Arrange -------------------------
    object_id = SampleData.get(object_name)

    # Store ids of the object and its children to check their state later
    object = sample_project_service._get_element_by_id(object_id)
    object_and_children_ids = object.get_ids()

    # Store previous parent and object/children states
    parent_state_before = object.parent.state
    objects_states_before: Dict[ProteusID, ProteusState] = {}
    for id in object_and_children_ids:
        object_states_before = sample_project_service._get_element_by_id(id)
        objects_states_before[id] = object_states_before.state


    # Find objects that are tracing the object or its children (sources)
    sources_ids = set()
    for target_id, sources in sample_project_service.traces_index.items():
        for source_id, _ in sources:
            # Add sources that point the object or its children but exclude
            # the object and its children themselves
            if (
                source_id not in object_and_children_ids
                and target_id in object_and_children_ids
            ):
                sources_ids.add(source_id)

    # Store previous sources states
    sources_states_before: Dict[ProteusID, ProteusState] = {}
    for source_id in sources_ids:
        source_states_before = sample_project_service._get_element_by_id(source_id)
        sources_states_before[source_id] = source_states_before.state

    # Store a copy of sources traces before the command execution
    # Just copy the traces that are tracing the object or its children
    sources_traces_before: Dict[ProteusID, Dict[ProteusID, TraceProperty]] = {}
    for source_id in sources_ids:
        source_dict: Dict[ProteusID, TraceProperty] = {}
        source = sample_project_service._get_element_by_id(source_id)
        for trace in source.get_traces():
            # Check if the trace is tracing the object or its children
            common_ids = [id for id in trace.value if id in object_and_children_ids]
            if len(common_ids) > 0:
                source_dict[trace.name] = trace
        sources_traces_before[source_id] = source_dict

    # Act -----------------------------
    delete_object_command = DeleteObjectCommand(object_id, sample_project_service)
    delete_object_command.redo()
    delete_object_command.undo()

    # Assert --------------------------
    # Check all states are restored
    assert all(
        [
            sample_project_service._get_element_by_id(id).state == state
            for id, state in objects_states_before.items()
        ]
    ), "All objects states must be restored to their previous state"

    # Check parent state is restored
    assert (
        object.parent.state == parent_state_before
    ), f"Parent object state must be restored to its previous state but it is {object.parent.state}"

    # Check sources states are restored
    assert all(
        [
            sample_project_service._get_element_by_id(id).state == state
            for id, state in sources_states_before.items()
        ]
    ), "All sources states must be restored to their previous state"

    # Check sources traces are the same as before redo
    for source_id, traces in sources_traces_before.items():
        for trace_name, trace in traces.items():
            # Get source trace
            source = sample_project_service._get_element_by_id(source_id)
            source_updated_trace = source.get_property(trace_name)
            assert source_updated_trace.value == trace.value, f"Updated trace {trace_name} of source {source_id} must be the same as before redo \
                (before: {trace.value}, after: {source_updated_trace.value}) \
                Current targets: {source_updated_trace.value} \
                Previous targets: {trace.value}\
                Ids: {object_and_children_ids}"
            
