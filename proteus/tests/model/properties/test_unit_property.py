# ==========================================================================
# File: test_unit_property.py
# Description: pytest file for PROTEUS unit properties
# Date: 26/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
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

from proteus.model.properties.unit_property import UnitProperty, Measurement
from proteus.model.properties import (
    PropertyFactory,
    VALUE_TAG,
    UNIT_TAG,
    UNIT_PROPERTY_TAG,
    DEFAULT_CATEGORY,
    DEFAULT_NAME,
)
from proteus.model import (
    NAME_ATTRIBUTE,
    CATEGORY_ATTRIBUTE,
    UNITS_ATTRIBUTE,
)

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def create_unit_property_element(
    units: str,
    value: float,
    unit: str,
) -> ET._Element:
    """
    Create an unit property XML element with the given parameters.

    :param units: Space-separated list of units.
    :param value: Value of the measurement.
    :param unit: Unit of the measurement.
    :return: The created XML element.
    """
    unit_property_element: ET._Element = ET.Element(UNIT_PROPERTY_TAG)

    unit_property_element.set(NAME_ATTRIBUTE, DEFAULT_NAME)
    unit_property_element.set(CATEGORY_ATTRIBUTE, DEFAULT_CATEGORY)
    # Tooltip, required and inmutable attributes are not tested here
    unit_property_element.set(UNITS_ATTRIBUTE, units)

    value_element: ET._Element = ET.SubElement(unit_property_element, VALUE_TAG)
    value_element.text = str(value)

    unit_element: ET._Element = ET.SubElement(unit_property_element, UNIT_TAG)
    unit_element.text = unit

    return unit_property_element


# --------------------------------------------------------------------------
# Measurement tests
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, unit, expected_value, expected_unit",
    [
        (1.0, "years", 1.0, "years"),
        (1, "years", 1.0, "years"),
        (-1.0, "years", -1.0, "years"),
        (-1, "years", -1.0, "years"),
        ("1.0", "years", 1.0, "years"),
        ("1", "years", 1.0, "years"),
        ("-1.0", "years", -1.0, "years"),
        ("-1", "years", -1.0, "years"),
    ],
)
def test_measurement_creation(
    value: float, unit: str, expected_value: float, expected_unit: str
) -> None:
    """
    It tests the creation of a measurement object.
    """
    # Arrange/Act ---------------------
    measurement: Measurement = Measurement(value=value, unit=unit)

    # Assert --------------------------
    assert (
        measurement.value == expected_value
    ), f"Measurement value '{measurement.value}' does not match expected value '{expected_value}'"
    assert (
        measurement.unit == expected_unit
    ), f"Measurement unit '{measurement.unit}' does not match expected unit '{expected_unit}'"


@pytest.mark.parametrize(
    "value, unit, expected_exception",
    [
        (1.0, None, AssertionError),  # Unit is None
        (1.0, 1, AssertionError),  # Unit is not a string
        (1.0, "", AssertionError),  # Unit is empty
        (1.0, " ", AssertionError),  # Unit is blank
        (1.0, "years days", AssertionError),  # Unit is not a single word
        ("1.0.0", "years", ValueError),  # Value is not a valid str
        ([], "years", ValueError),  # Value is not a int, float or string
        (None, "years", AssertionError),  # Value is None
    ],
)
def test_measurement_creation_negative(value, unit, expected_exception) -> None:
    """
    It tests the creation of a measurement object with invalid parameters.
    """
    with pytest.raises(expected_exception):
        Measurement(value=value, unit=unit)


# --------------------------------------------------------------------------
# Unit property tests
# --------------------------------------------------------------------------


def test_unit_property_creation_from_xml_element() -> None:
    """
    It tests the creation of a unit property from an XML element.
    """
    # Arrange -------------------------
    units: str = "years days hours"
    value: float = 1.0
    unit: str = "years"

    # Create XML element for unit property
    unit_property_element: ET._Element = create_unit_property_element(
        units, value, unit
    )

    # Act -----------------------------
    # Create unit property from XML element
    unit_property: UnitProperty = PropertyFactory.create(unit_property_element)

    # Assert --------------------------
    assert (
        unit_property.name == DEFAULT_NAME
    ), f"Unit property name '{unit_property.name}' does not match expected name '{DEFAULT_NAME}'"
    assert (
        unit_property.category == DEFAULT_CATEGORY
    ), f"Unit property category '{unit_property.category}' does not match expected category '{DEFAULT_CATEGORY}'"
    assert (
        unit_property.units == units.split()
    ), f"Unit property units '{unit_property.units}' do not match expected units '{units}'"

    measurement: Measurement = Measurement(value=value, unit=unit)
    assert (
        unit_property.value == measurement
    ), f"Unit property value '{unit_property.value}' does not match expected value '{measurement}'"


@pytest.mark.parametrize(
    "units, value, unit, expected_units, expected_value, expected_unit",
    [
        ("years days hours", 1.0, "years", ["years", "days", "hours"], 1.0, "years"),
        ("years", 1.0, "years", ["years"], 1.0, "years"),
        ("years", 1.0, "seconds", ["years"], 1.0, "years"),  # Unit is not in units
        ("years days", 1.0, "seconds", ["years", "days"], 1.0, "years"),
    ],
)
def test_trace_creation(
    units, value, unit, expected_units, expected_value, expected_unit
) -> None:
    """
    Test the creation of an unit property using its constructor.
    """
    # Arrange -------------------------
    expected_measurement: Measurement = Measurement(
        value=expected_value, unit=expected_unit
    )

    # Act -----------------------------
    # Create unit property
    unit_property: UnitProperty = UnitProperty(
        units=units,
        value=Measurement(value=value, unit=unit),
    )

    # Assert --------------------------
    assert (
        unit_property.units == expected_units
    ), f"Unit property units '{unit_property.units}' do not match expected units '{expected_units}'"

    assert (
        unit_property.value == expected_measurement
    ), f"Unit property value '{unit_property.value}' does not match expected value '{expected_measurement}'"


def test_trace_creation_unit_not_in_units() -> None:
    """
    Test the creation of an unit property using its constructor with a unit
    that is not in the units list. It should assign the first unit in the list.
    """
    # Arrange -------------------------
    units: str = "years days"
    value: float = 1.0
    unit: str = "seconds"

    expected_measurement: Measurement = Measurement(value=value, unit=units.split()[0])

    # Act -----------------------------
    unit_property = UnitProperty(
        units=units,
        value=Measurement(value=value, unit=unit),
    )

    # Assert --------------------------
    assert (
        unit_property.value == expected_measurement
    ), f"Unit property value '{unit_property.value}' does not match expected value '{expected_measurement}'"


def test_trace_creation_wrong_value_type() -> None:
    """
    Test the creation of an unit property using its constructor with a wrong
    value type. It should assign the default value.
    """
    # Arrange -------------------------
    units: str = "years days"
    value: str = "1.0"

    expected_measurement: Measurement = Measurement(value=0, unit=units.split()[0])

    # Act -----------------------------
    unit_property = UnitProperty(
        units=units,
        value=value,
    )

    # Assert --------------------------
    assert (
        unit_property.value == expected_measurement
    ), f"Unit property value '{unit_property.value}' does not match expected value '{expected_measurement}'"


def test_generate_xml() -> None:
    """
    Test the generation of an XML element from an unit property.
    """
    # Arrange -------------------------
    unit_property_element: ET._Element = create_unit_property_element(
        "years days hours", 1.0, "years"
    )
    unit_property: UnitProperty = PropertyFactory.create(unit_property_element)

    # Act -----------------------------
    generated_element: ET._Element = unit_property.generate_xml()

    # Assert --------------------------
    assert ET.tostring(generated_element) == ET.tostring(
        unit_property_element
    ), "Generated XML element does not match the expected XML element"
