# ==========================================================================
# File: test_properties.py
# Description: pytest file for PROTEUS properties (general)
# Date: 22/10/2022
# Version: 0.2
# Author: Amador Durán Toro
#         José María Delgado Sánchez
# ==========================================================================
# Update: 22/10/2022 (Amador)
# Description:
# - Common code extracted as fixtures.
# ==========================================================================
# Update: 27/12/2024 (José María)
# Description:
# - Added test for post_init, generate_xml methods and other properties
#   general tests.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties import (
    DEFAULT_NAME,
    DEFAULT_CATEGORY,
    PropertyFactory,
    StringProperty,
)

# --------------------------------------------------------------------------
# Test specific imports
# --------------------------------------------------------------------------

import proteus.tests.fixtures as fixtures

# --------------------------------------------------------------------------
# General property tests
# --------------------------------------------------------------------------
# NOTE: StringProperty is being used as reference since Property is an abstract
# class. StringProperty is the simplest concrete class that inherits from
# Property.


@pytest.mark.parametrize("property_tag", ["WrongProperty", "wrong_property"])
def test_wrong_property_tag(property_tag):
    """
    It tests that PropertyFactory returns None when the XML
    element is not a property element.
    """
    # Arrange -------------------------
    property_element = fixtures.create_property_element(property_tag=property_tag)

    # Act -----------------------------
    property = PropertyFactory.create(property_element)

    # Assert --------------------------
    assert (
        property is None
    ), f"Expected PropertyFactory to return None for property tag '{property_tag}', got '{property}'"


@pytest.mark.parametrize(
    "tooltip, expected_tooltip",
    [(str(), str()), ("test_tooltip", "test_tooltip")],
)
@pytest.mark.parametrize(
    "required, expected_required",
    [(True, True), (False, False), ("dummy", False)],
)
@pytest.mark.parametrize(
    "inmutable, expected_inmutable",
    [(True, True), (False, False), ("dummy", False)],
)
def test_property_factory(
    tooltip,
    expected_tooltip,
    required,
    expected_required,
    inmutable,
    expected_inmutable,
):
    """
    It tests that the PropertyFactory returns a Property object
    with the correct attribute values.

    Name and category values are fix since property factory is not
    meant to set them to a default value in case they are not provided.
    """
    # Arrange -------------------------
    property_element = fixtures.create_property_element(
        tooltip=tooltip, required=required, inmutable=inmutable
    )
    property_element.text = ET.CDATA("")

    # Act -----------------------------
    _property = PropertyFactory.create(property_element)

    # Assert --------------------------
    assert (
        _property.name == DEFAULT_NAME
    ), f"Property name '{_property.name}' does not match expected name '{DEFAULT_NAME}'"
    assert (
        _property.category == DEFAULT_CATEGORY
    ), f"Property category '{_property.category}' does not match expected category '{DEFAULT_CATEGORY}'"
    assert (
        _property.tooltip == expected_tooltip
    ), f"Property tooltip '{_property.tooltip}' does not match expected tooltip '{expected_tooltip}'"
    assert (
        _property.required == expected_required
    ), f"Property required '{_property.required}' does not match expected required '{expected_required}'"
    assert (
        _property.inmutable == expected_inmutable
    ), f"Property inmutable '{_property.inmutable}' does not match expected inmutable '{expected_inmutable}'"


@pytest.mark.parametrize(
    "name, expected_name",
    [(str(), DEFAULT_NAME), ("test_name", "test_name")],
)
@pytest.mark.parametrize(
    "category, expected_category",
    [(str(), DEFAULT_CATEGORY), ("test_category", "test_category")],
)
@pytest.mark.parametrize(
    "tooltip, expected_tooltip",
    [(str(), str()), ("test_tooltip", "test_tooltip"), (None, str())],
)
@pytest.mark.parametrize(
    "required, expected_required",
    [(True, True), (False, False), (None, False)],
)
@pytest.mark.parametrize(
    "inmutable, expected_inmutable",
    [(True, True), (False, False), (None, False)],
)
def test_property_post_init(
    name,
    expected_name,
    category,
    expected_category,
    tooltip,
    expected_tooltip,
    required,
    expected_required,
    inmutable,
    expected_inmutable,
):
    """
    It tests the post-init method of the Property class. Some attributes may
    be set to default values if they are not provided (provided as None).
    """
    # Arrange/Act ---------------------
    _property = StringProperty(
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
    )

    # Assert ---------------------------
    assert (
        _property.name == expected_name
    ), f"Property name '{_property.name}' does not match expected name '{expected_name}'"
    assert (
        _property.category == expected_category
    ), f"Property category '{_property.category}' does not match expected category '{expected_category}'"
    assert (
        _property.tooltip == expected_tooltip
    ), f"Property tooltip '{_property.tooltip}' does not match expected tooltip '{expected_tooltip}'"
    assert (
        _property.required == expected_required
    ), f"Property required '{_property.required}' does not match expected required '{expected_required}'"
    assert (
        _property.inmutable == expected_inmutable
    ), f"Property inmutable '{_property.inmutable}' does not match expected inmutable '{expected_inmutable}'"


@pytest.mark.parametrize(
    "tooltip",
    [str(), "test_tooltip"],
)
@pytest.mark.parametrize(
    "required",
    [True, False],
)
@pytest.mark.parametrize(
    "inmutable",
    [True, False],
)
def test_generate_xml(tooltip, required, inmutable) -> None:
    """
    Test generated xml is correct according to the expected structure. Some
    attributes must not be present if the are certain values (ej. inmutable=False).
    """
    # Arrange -------------------------
    property_element = fixtures.create_property_element(
        tooltip=tooltip, required=required, inmutable=inmutable
    )
    property_element.text = ET.CDATA("")

    _property = PropertyFactory.create(property_element)

    # Act -----------------------------
    generated_xml = _property.generate_xml()

    # Assert --------------------------
    assert ET.tostring(generated_xml) == ET.tostring(
        property_element
    ), f"Generated XML '{ET.tostring(generated_xml)}' does not match expected XML '{ET.tostring(property_element)}'"


def test_clone() -> None:
    """
    Test that the clone method returns a new object with the same attributes
    but different value (new value provided as argument).
    """
    # Arrange -------------------------
    new_value = "new_value"

    original_property = StringProperty()

    # Act -----------------------------
    cloned_property = original_property.clone(new_value)

    # Assert --------------------------
    assert (
        cloned_property is not original_property
    ), f"Expected cloned property to be different from original property, got '{cloned_property}'"

    assert (
        cloned_property.name == original_property.name
    ), f"Expected cloned property name '{cloned_property.name}' to be the same as original property name '{original_property.name}'"

    assert (
        cloned_property.category == original_property.category
    ), f"Expected cloned property category '{cloned_property.category}' to be the same as original property category '{original_property.category}'"

    assert (
        cloned_property.tooltip == original_property.tooltip
    ), f"Expected cloned property tooltip '{cloned_property.tooltip}' to be the same as original property tooltip '{original_property.tooltip}'"

    assert (
        cloned_property.required == original_property.required
    ), f"Expected cloned property required '{cloned_property.required}' to be the same as original property required '{original_property.required}'"

    assert (
        cloned_property.inmutable == original_property.inmutable
    ), f"Expected cloned property inmutable '{cloned_property.inmutable}' to be the same as original property inmutable '{original_property.inmutable}'"

    assert (
        cloned_property.value == new_value
        and cloned_property.value != original_property.value
    ), f"Expected cloned property value '{cloned_property.value}' to be the same as new value '{new_value}'"


def test_clone_with_no_value() -> None:
    """
    Test that the clone property is a different object even when the value is not provided.
    """
    # Arrange -------------------------
    original_property = StringProperty()

    # Act -----------------------------
    cloned_property = original_property.clone()

    # Assert --------------------------
    assert (
        cloned_property is not original_property
    ), f"Expected cloned property to be different from original property, got '{cloned_property}'"

    assert id(cloned_property) != id(
        original_property
    ), f"Expected cloned property to be different from original property, got '{id(cloned_property)}' and '{id(original_property)}"


def test_compare_equal() -> None:
    """
    Test that the compare method returns True when the value of the properties is the same.
    """
    # Arrange -------------------------
    original_property = StringProperty()

    # Act -----------------------------
    equal_property = StringProperty()

    # Assert --------------------------
    assert original_property.compare(
        equal_property
    ), f"Expected properties to be equal, got '{original_property}' and '{equal_property}'"


@pytest.mark.parametrize(
    "name, category, tooltip, required, inmutable, value",
    [
        # One different attribute at a time
        ("test_name", DEFAULT_CATEGORY, str(), False, False, ""),
        (DEFAULT_NAME, "test_category", str(), False, False, ""),
        (DEFAULT_NAME, DEFAULT_CATEGORY, "test_tooltip", False, False, ""),
        (DEFAULT_NAME, DEFAULT_CATEGORY, str(), True, False, ""),
        (DEFAULT_NAME, DEFAULT_CATEGORY, str(), False, True, ""),
        (DEFAULT_NAME, DEFAULT_CATEGORY, str(), False, False, "test_value"),
    ],
)
def test_compare_different(name, category, tooltip, required, inmutable, value) -> None:
    """
    Test that the compare method returns False when the value of the properties is different.
    """
    # Arrange -------------------------
    original_property = StringProperty()

    different_property = StringProperty(
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
        value=value,
    )

    # Act -----------------------------
    result = original_property.compare(different_property)

    # Assert --------------------------
    assert (
        not result
    ), f"Expected properties to be different, got '{original_property}' and '{different_property}'"


@pytest.mark.parametrize(
    "other",
    [
        "dummy",
        1,
        1.0,
        True,
        False,
        [],
        {},
        (),
        set(),
    ],
)
def test_compare_wrong_type(other) -> None:
    """
    Test that the compare method returns False when the other object is not a property.
    """
    # Arrange -------------------------
    original_property = StringProperty()

    # Act -----------------------------
    result = original_property.compare(other)

    # Assert --------------------------
    assert (
        not result
    ), f"Expected compare to return False for other '{other}', got '{result}'"
