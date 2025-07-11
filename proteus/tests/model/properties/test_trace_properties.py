# ==========================================================================
# File: test_trace_properties.py
# Description: pytest file for PROTEUS trace properties
# Date: 16/11/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================
# Update: 27/12/2024 (José María)
# Description:
# - Test optimization to avoid unnecessary checks already performed by the
#   super class and remove unnecessary parametrizations.
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
    ACCEPTED_TARGETS_ATTRIBUTE,
    EXCLUDED_TARGETS_ATTRIBUTE,
    TRACE_TYPE_ATTRIBUTE,
    PROTEUS_ANY,
    MAX_TARGETS_NUMBER_ATTRIBUTE,
)

# --------------------------------------------------------------------------
# Tests specific imports
# --------------------------------------------------------------------------

import proteus.tests.fixtures as fixtures

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

DUMMY_TARGET_LIST_EMPTY = []
DUMMY_TARGET_LIST_1 = ["target1"]
DUMMY_TARGET_LIST_2 = ["target1", "target2"]
DUMMY_TARGET_LIST_3 = ["target1", "target2", "target3"]


def create_trace_element(
    # Specific trace parameters
    targets: List[str],
    accepted_targets: str = PROTEUS_ANY,
    excluded_targets: str = str(),
    trace_type: str = DEFAULT_TRACE_TYPE,
    max_targets: int = NO_TARGETS_LIMIT,
    # General property parameters
    name: str = DEFAULT_NAME,
    category: str = DEFAULT_CATEGORY,
    tooltip: str = str(),
    required: bool | str = False,
    inmutable: bool | str = False,
) -> ET._Element:
    """
    Create a trace XML element with the given parameters.

    :param targets: List of targets for the trace.
    :param accepted_targets: Accepted targets for the trace. Default is PROTEUS_ANY.
    :param excluded_targets: Excluded targets for the trace. Default is None.
    :param trace_type: Type of the trace. Default is DEFAULT_TRACE_TYPE.
    :param max_targets: Maximum number of targets for the trace. Default is None.
    :param name: Name of the property. Default is DEFAULT_NAME.
    :param category: Category of the property. Default is DEFAULT_CATEGORY.
    :param tooltip: Tooltip of the property. Default is empty string.
    :param required: Required attribute of the property. Default is False.
    :param inmutable: Inmutable attribute of the property. Default is False.
    :return: The created XML element.
    """
    trace_element: ET._Element = fixtures.create_property_element(
        property_tag=TRACE_PROPERTY_TAG,
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
    )

    trace_element.set(ACCEPTED_TARGETS_ATTRIBUTE, accepted_targets)

    if excluded_targets:
        trace_element.set(EXCLUDED_TARGETS_ATTRIBUTE, excluded_targets)

    trace_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    if max_targets != NO_TARGETS_LIMIT and max_targets > 0:
        trace_element.set(MAX_TARGETS_NUMBER_ATTRIBUTE, str(max_targets))

    # Add dummy subelemnts
    for target in targets:
        target_element: ET._Element = ET.SubElement(trace_element, TRACE_TAG)
        target_element.set(TARGET_ATTRIBUTE, target)
        target_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    return trace_element


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "targets, expected_targets",
    [
        (["target1", "target2", ""], ["target1", "target2"]),
        (DUMMY_TARGET_LIST_EMPTY, DUMMY_TARGET_LIST_EMPTY),
        (DUMMY_TARGET_LIST_3, DUMMY_TARGET_LIST_3),
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
    "max_targets, expected_max_targets",
    [
        (5, 5),
        (None, NO_TARGETS_LIMIT),
        ("test", NO_TARGETS_LIMIT),
    ],
)
def test_trace_property_factory(
    mocker,
    targets,
    expected_targets,
    accepted_targets,
    expected_accepted_targets,
    excluded_targets,
    expected_excluded_targets,
    trace_type,
    expected_trace_type,
    max_targets,
    expected_max_targets,
) -> None:
    """
    It tests the creation of a unit property from an XML element using the
    PropertyFactory. It is important to check every attribute of the trace
    property in order to ensure that the constructor is being called correctly.
    """
    # Arrange -------------------------
    name: str = "test_name"
    category: str = "test_category"
    tooltip: str = "test_tooltip"
    required: bool = True
    inmutable: bool = True

    # Mock the TraceProperty constructor
    mocker.patch(
        "proteus.model.properties.trace_property.TraceProperty.__init__",
        return_value=None,
    )

    # NOTE: Create trace element function is not used here in order
    # to test specific property factory behavior
    trace_element: ET._Element = fixtures.create_property_element(
        TRACE_PROPERTY_TAG,
        name,
        category,
        tooltip,
        required,
        inmutable,
    )

    if accepted_targets:
        trace_element.set(ACCEPTED_TARGETS_ATTRIBUTE, accepted_targets)

    if excluded_targets:
        trace_element.set(EXCLUDED_TARGETS_ATTRIBUTE, excluded_targets)

    if trace_type:
        trace_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    # Max_targets attributes
    if max_targets is not None:
        trace_element.set(MAX_TARGETS_NUMBER_ATTRIBUTE, str(max_targets))

    # Add dummy subelemnts
    for target in targets:
        target_element: ET._Element = ET.SubElement(trace_element, TRACE_TAG)
        target_element.set(TARGET_ATTRIBUTE, target)
        target_element.set(TRACE_TYPE_ATTRIBUTE, trace_type)

    # Act -----------------------------
    PropertyFactory.create(trace_element)

    # Assert --------------------------
    # Check TraceProperty constructor call
    TraceProperty.__init__.assert_called_once_with(
        name,
        category,
        expected_targets,
        tooltip,
        required,
        inmutable,
        expected_accepted_targets,
        expected_excluded_targets,
        expected_trace_type,
        expected_max_targets,
    )


@pytest.mark.parametrize(
    "targets, expected_targets, max_targets, expected_max_targets",
    [
        # Valid
        ([], [], -1, -1),
        (["target1", "target2"], ["target1", "target2"], 10, 10),
        # Exceeding targets limit
        (["target1", "target2", "target3"], ["target1", "target2"], 2, 2),
        # Invalid max targets
        ([], [], 0, -1),
        ([], [], -50, -1),
        # Invalid targets
        ("", [], -1, -1),
    ],
)
@pytest.mark.parametrize(
    "accepted_targets, expected_accepted_targets, excluded_targets, expected_excluded_targets, trace_type, expected_trace_type",
    [
        # Valid
        (
            ["cls1", "cls2"],
            ["cls1", "cls2"],
            ["ecls1", "ecls2"],
            ["ecls1", "ecls2"],
            "type",
            "type",
        ),
        (["cls1", "cls2"], ["cls1", "cls2"], [], [], "type", "type"),
        # Wrong accepted targets
        ("test", [PROTEUS_ANY], [], [], "type", "type"),
        ([], [PROTEUS_ANY], [], [], "type", "type"),
        # Wrong excluded targets
        (["cls1", "cls2"], ["cls1", "cls2"], "test", [], "type", "type"),
        # Wrong trace type
        (["cls1", "cls2"], ["cls1", "cls2"], [], [], None, DEFAULT_TRACE_TYPE),
    ],
)
def test_trace_creation(
    targets,
    expected_targets,
    max_targets,
    expected_max_targets,
    accepted_targets,
    expected_accepted_targets,
    excluded_targets,
    expected_excluded_targets,
    trace_type,
    expected_trace_type,
) -> None:
    """
    Test creation of trace property using the constructor.
    """
    # Arrange -------------------------
    name: str = "test_name"
    category: str = "test_category"
    tooltip: str = "test_tooltip"
    required: bool = True
    inmutable: bool = True

    # Act -----------------------------
    trace: TraceProperty = TraceProperty(
        name,
        category,
        targets,
        tooltip,
        required,
        inmutable,
        accepted_targets,
        excluded_targets,
        trace_type,
        max_targets,
    )

    # Assert --------------------------
    assert (
        trace.value == expected_targets
    ), f"Trace property value (targets) '{trace.value}' does not match expected value '{expected_targets}'"
    assert (
        trace.maxTargetsNumber == expected_max_targets
    ), f"Trace property max targets number '{trace.maxTargetsNumber}' does not match expected value '{expected_max_targets}'"
    assert (
        trace.acceptedTargets == expected_accepted_targets
    ), f"Trace property accepted targets '{trace.acceptedTargets}' does not match expected value '{expected_accepted_targets}'"
    assert (
        trace.excludedTargets == expected_excluded_targets
    ), f"Trace property excluded targets '{trace.excludedTargets}' does not match expected value '{expected_excluded_targets}'"
    assert (
        trace.traceType == expected_trace_type
    ), f"Trace property trace type '{trace.traceType}' does not match expected value '{expected_trace_type}'"


def test_trace_property_factory_trace_without_attribute(mocker) -> None:
    """
    It tests the creation of a trace property from an XML element without
    the trace attributes. The trace property should be created with the
    default values.
    """
    # Arrange -------------------------
    name: str = "test_name"
    category: str = "test_category"
    tooltip: str = "test_tooltip"
    required: bool = True
    inmutable: bool = True
    targets = DUMMY_TARGET_LIST_3

    # Mock the TraceProperty constructor
    mocker.patch(
        "proteus.model.properties.trace_property.TraceProperty.__init__",
        return_value=None,
    )

    trace_element: ET._Element = create_trace_element(
        targets,
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
    )

    # Add trace tag without target attribute
    ET.SubElement(trace_element, TRACE_TAG)

    # Act -----------------------------
    PropertyFactory.create(trace_element)

    # Assert --------------------------
    # Check there are 4 trace tags in the XML element
    assert (
        len(trace_element.findall(TRACE_TAG)) == len(targets) + 1
    ), f"There should be {len(targets) + 1} trace tags in the XML element"

    # Check TraceProperty constructor call
    TraceProperty.__init__.assert_called_once_with(
        name,
        category,
        targets,
        tooltip,
        required,
        inmutable,
        [PROTEUS_ANY],
        [],
        DEFAULT_TRACE_TYPE,
        NO_TARGETS_LIMIT,
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
@pytest.mark.parametrize(
    "exclude_targets",
    [
        "",
        "class1",
        "class1 class2",
    ],
)
@pytest.mark.parametrize(
    "max_targets_number",
    [-1, 0, 10],
)
def test_generate_xml(targets, exclude_targets, max_targets_number) -> None:
    """
    Tests XML generation for traces with different number of targets (0 to 3).
    """
    # Arrange -------------------------
    name = "test_name"
    category = "test_category"
    tooltip = "test_tooltip"
    required = True
    inmutable = True
    accepted_targets = "class1 class2"
    trace_type = "test-type"

    # Create trace from XML element
    trace_element = create_trace_element(
        targets,
        accepted_targets,
        exclude_targets,
        trace_type,
        max_targets_number,
        name,
        category,
        tooltip,
        required,
        inmutable,
    )
    trace: TraceProperty = PropertyFactory.create(trace_element)

    # Act -----------------------------
    # Generate XML element
    generated_trace_element = trace.generate_xml()

    # Assert --------------------------
    # Compare XML converted to string
    assert ET.tostring(generated_trace_element) == ET.tostring(
        trace_element
    ), f"Generated XML element '{ET.tostring(generated_trace_element)}' does not match expected XML element '{ET.tostring(trace_element)}'"
