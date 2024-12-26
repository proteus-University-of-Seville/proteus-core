# ==========================================================================
# File: test_trace_properties.py
# Description: pytest file for PROTEUS trace properties
# Date: 16/11/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties.trace_property import TraceProperty, NO_TARGETS_LIMIT
from proteus.model.properties import (
    PropertyFactory,
    TRACE_TAG,
    TRACE_PROPERTY_TAG,
    DEFAULT_TRACE_TYPE,
    DEFAULT_CATEGORY,
    DEFAULT_NAME,
)
from proteus.model import (
    TARGET_ATTRIBUTE,
    NAME_ATTRIBUTE,
    CATEGORY_ATTRIBUTE,
    ACCEPTED_TARGETS_ATTRIBUTE,
    EXCLUDED_TARGETS_ATTRIBUTE,
    TRACE_TYPE_ATTRIBUTE,
    PROTEUS_ANY,
    TOOLTIP_ATTRIBUTE,
    MAX_TARGETS_NUMBER_ATTRIBUTE,
)

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

DUMMY_TARGET_LIST_EMPTY = []
DUMMY_TARGET_LIST_1 = ["target1"]
DUMMY_TARGET_LIST_2 = ["target1", "target2"]
DUMMY_TARGET_LIST_3 = ["target1", "target2", "target3"]


def create_trace_element(
    dummy_targets: List[str],
    name: str = DEFAULT_NAME,
    category: str = DEFAULT_CATEGORY,
    accepted_targets: str = PROTEUS_ANY,
    excluded_targets: str = None,
    trace_type: str = DEFAULT_TRACE_TYPE,
    tooltip: str = None,
    max_targets: int = None,
) -> ET._Element:
    """
    Create a trace XML element with the given parameters.
    """
    trace_element: ET._Element = ET.Element(TRACE_PROPERTY_TAG)
    # Add attributes
    trace_element.set(NAME_ATTRIBUTE, name)
    trace_element.set(CATEGORY_ATTRIBUTE, category)

    if tooltip is not None:
        trace_element.set(TOOLTIP_ATTRIBUTE, tooltip)

    trace_element.set(ACCEPTED_TARGETS_ATTRIBUTE, accepted_targets)

    if excluded_targets is not None:
        trace_element.set(EXCLUDED_TARGETS_ATTRIBUTE, excluded_targets)

    trace_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    # Max_targets attributes
    if max_targets is not None:
        trace_element.set(MAX_TARGETS_NUMBER_ATTRIBUTE, str(max_targets))

    # Add dummy subelemnts
    for dummy_target in dummy_targets:
        target_element: ET._Element = ET.SubElement(trace_element, TRACE_TAG)
        target_element.set(TARGET_ATTRIBUTE, dummy_target)
        target_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    return trace_element


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "name, expected_name",
    [("test name", "test name"), (str(), DEFAULT_NAME)],
)
@pytest.mark.parametrize(
    "category, expected_category",
    [
        ("test category", "test category"),
        (str(), DEFAULT_CATEGORY),
    ],
)
@pytest.mark.parametrize(
    "accepted_targets, expected_accepted_targets",
    [
        ("target1", ["target1"]),
        ("target1 target2 target3", ["target1", "target2", "target3"]),
        (str(), [PROTEUS_ANY]),
    ],
)
@pytest.mark.parametrize(
    "excluded_targets, expected_excluded_targets",
    [
        ("target1", ["target1"]),
        ("target1 target2 target3", ["target1", "target2", "target3"]),
        (str(), []),
    ],
)
@pytest.mark.parametrize(
    "trace_type, expected_trace_type",
    [("test-type", "test-type"), (str(), DEFAULT_TRACE_TYPE)],
)
@pytest.mark.parametrize(
    "dummy_targets, expected_targets",
    [
        (DUMMY_TARGET_LIST_EMPTY, DUMMY_TARGET_LIST_EMPTY),
        (DUMMY_TARGET_LIST_3, DUMMY_TARGET_LIST_3),
    ],
)
@pytest.mark.parametrize(
    "tooltip, expected_tooltip",
    [("dummy.tooltip", "dummy.tooltip"), (None, str())],
)
@pytest.mark.parametrize(
    "max_targets_number, expected_max_targets_number",
    [
        (5, 5),
        (None, NO_TARGETS_LIMIT),
        (0, NO_TARGETS_LIMIT),
        (-100, NO_TARGETS_LIMIT),
        ("test", NO_TARGETS_LIMIT),
    ],
)
def test_trace_creation(
    name,
    expected_name,
    category,
    expected_category,
    accepted_targets,
    expected_accepted_targets,
    excluded_targets,
    expected_excluded_targets,
    trace_type,
    expected_trace_type,
    dummy_targets,
    expected_targets,
    tooltip,
    expected_tooltip,
    max_targets_number,
    expected_max_targets_number,
):
    """
    Tests trace creation from an XML element.
    """
    # Act -----------------------------
    # Create trace from XML element
    trace_element = create_trace_element(
        dummy_targets,
        name,
        category,
        accepted_targets,
        excluded_targets,
        trace_type,
        tooltip,
        max_targets_number,
    )
    trace: TraceProperty = PropertyFactory.create(trace_element)

    # Assert --------------------------
    # Check trace attributes
    assert (
        trace.name == expected_name
    ), f"Trace name '{trace.name}' does not match expected name '{expected_name}'"
    assert (
        trace.category == expected_category
    ), f"Trace category '{trace.category}' does not match expected category '{expected_category}'"
    assert (
        trace.acceptedTargets == expected_accepted_targets
    ), f"Trace accepted targets '{trace.acceptedTargets}' do not match expected accepted targets '{expected_accepted_targets}'"
    assert (
        trace.traceType == expected_trace_type
    ), f"Trace type '{trace.traceType}' does not match expected traceType '{expected_trace_type}'"
    assert (
        trace.value == expected_targets
    ), f"Trace targets '{trace.value}' do not match expected targets '{expected_targets}'"
    assert (
        trace.excludedTargets == expected_excluded_targets
    ), f"Trace excluded targets '{trace.excludedTargets}' do not match expected excluded targets '{expected_excluded_targets}'"
    assert (
        trace.tooltip == expected_tooltip
    ), f"Trace tooltip '{trace.tooltip}' does not match expected tooltip '{expected_tooltip}'"
    assert (
        trace.maxTargetsNumber == expected_max_targets_number
    ), f"Trace max targets number '{trace.maxTargetsNumber}' does not match expected max targets number '{expected_max_targets_number}'"


@pytest.mark.parametrize(
    "old_targets, new_targets",
    [
        (DUMMY_TARGET_LIST_EMPTY, DUMMY_TARGET_LIST_2),
        (DUMMY_TARGET_LIST_3, DUMMY_TARGET_LIST_1),
        (DUMMY_TARGET_LIST_2, DUMMY_TARGET_LIST_EMPTY),
    ],
)
def test_trace_clone(old_targets: List, new_targets: List):
    """
    Tests trace cloning. Ensure that the new targets are set correctly and old attributes are kept.
    Also compares the ids of the original and the cloned trace to ensure they are different.

    NOTE: Do not check if creation was successful. That is tested in test_trace_creation.
    """
    # Arrange -------------------------
    # Create trace from XML element
    trace_element = create_trace_element(old_targets)
    trace: TraceProperty = PropertyFactory.create(trace_element)

    # Act -----------------------------
    # Clone trace
    cloned_trace: TraceProperty = trace.clone(new_targets)

    # Assert --------------------------
    # Check trace attributes
    assert (
        cloned_trace.name == trace.name
    ), f"Cloned trace name '{cloned_trace.name}' does not match original name '{trace.name}'"
    assert (
        cloned_trace.category == trace.category
    ), f"Cloned trace category '{cloned_trace.category}' does not match original category '{trace.category}'"
    assert (
        cloned_trace.acceptedTargets == trace.acceptedTargets
    ), f"Cloned trace accepted targets '{cloned_trace.acceptedTargets}' do not match original accepted targets '{trace.acceptedTargets}'"
    assert (
        cloned_trace.excludedTargets == trace.excludedTargets
    ), f"Cloned trace excluded targets '{cloned_trace.excludedTargets}' do not match original excluded targets '{trace.excludedTargets}'"
    assert (
        cloned_trace.traceType == trace.traceType
    ), f"Cloned trace type '{cloned_trace.traceType}' does not match original traceType '{trace.traceType}'"
    assert (
        cloned_trace.value == new_targets
    ), f"Cloned trace targets '{cloned_trace.value}' do not match new targets '{new_targets}'"

    # Check ProteusTrace objects ids are different after cloning
    assert id(cloned_trace) != id(trace), (
        f"Cloned ProteusTrace object id ({id(cloned_trace)}) is the same as the original ({id(trace)}), "
        f"but it should be different"
    )


@pytest.mark.parametrize(
    "targets",
    [
        DUMMY_TARGET_LIST_EMPTY,
        DUMMY_TARGET_LIST_1,
        DUMMY_TARGET_LIST_2,
        DUMMY_TARGET_LIST_3,
    ],
)
def test_generate_xml(targets):
    """
    Tests XML generation for traces with different number of targets (0 to 3).
    """
    # Arrange -------------------------
    # Create trace from XML element
    trace_element = create_trace_element(targets)
    trace: TraceProperty = PropertyFactory.create(trace_element)

    # Act -----------------------------
    # Generate XML element
    generated_trace_element = trace.generate_xml()

    # Assert --------------------------
    # Compare XML converted to string
    assert ET.tostring(generated_trace_element) == ET.tostring(
        trace_element
    ), f"Generated XML element '{ET.tostring(generated_trace_element)}' does not match expected XML element '{ET.tostring(trace_element)}'"

    # NOTE: This might be redundant since the previous assertion checks the whole XML element, consider removing string comparison
    # Check trace attributes
    assert (
        generated_trace_element.tag == TRACE_PROPERTY_TAG
    ), f"Generated trace tag '{generated_trace_element.tag}' does not match expected tag '{TRACE_PROPERTY_TAG}'"
    assert (
        generated_trace_element.attrib[NAME_ATTRIBUTE] == trace.name
    ), f"Generated trace name '{generated_trace_element.attrib[NAME_ATTRIBUTE]}' does not match expected name '{trace.name}'"
    assert (
        generated_trace_element.attrib[CATEGORY_ATTRIBUTE] == trace.category
    ), f"Generated trace category '{generated_trace_element.attrib[CATEGORY_ATTRIBUTE]}' does not match expected category '{trace.category}'"
    assert generated_trace_element.attrib[ACCEPTED_TARGETS_ATTRIBUTE] == " ".join(
        trace.acceptedTargets
    ), f"Generated trace accepted targets '{generated_trace_element.attrib[ACCEPTED_TARGETS_ATTRIBUTE]}' do not match expected accepted targets '{trace.acceptedTargets}'"
    assert (
        generated_trace_element.attrib[TRACE_TYPE_ATTRIBUTE] == trace.traceType
    ), f"Generated trace type '{generated_trace_element.attrib[TRACE_TYPE_ATTRIBUTE]}' does not match expected traceType '{trace.traceType}'"

    # Check trace targets
    generated_targets = [
        target_element.attrib[TARGET_ATTRIBUTE]
        for target_element in generated_trace_element
    ]
    assert (
        generated_targets == trace.value
    ), f"Generated trace targets '{generated_targets}' do not match expected targets '{trace.value}'"


@pytest.mark.parametrize(
    "max_targets_number",
    [1, 2, 3, 100],
)
def test_generate_xml_max_targets_number(max_targets_number):
    """
    Tests XML generation for traces with different max targets numbers.
    """
    # Arrange -------------------------
    dummy_target_list = DUMMY_TARGET_LIST_3
    # Create trace from XML element
    trace_element = create_trace_element(
        dummy_target_list, max_targets=max_targets_number
    )
    trace: TraceProperty = PropertyFactory.create(trace_element)

    # Act -----------------------------
    # Generate XML element
    generated_trace_element = trace.generate_xml()

    # Assert --------------------------
    targets_elements = generated_trace_element.findall(TRACE_TAG)

    # Check max targets number attribute
    assert (
        len(targets_elements) <= max_targets_number
    ), f"Generated trace has {len(targets_elements)} targets, but it should have less or equal to {max_targets_number}"

    for i, target_element in enumerate(targets_elements):
        assert target_element.get(TARGET_ATTRIBUTE) == dummy_target_list[i], (
            f"Generated target '{target_element.get(TARGET_ATTRIBUTE)}' does not match expected target '{dummy_target_list[i]}'"
            f"Generated targets must be '{dummy_target_list[:max_targets_number]}'"
        )
