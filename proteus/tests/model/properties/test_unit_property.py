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
    DEFAULT_NAME,
    DEFAULT_CATEGORY,
)
from proteus.model import UNITS_ATTRIBUTE

# --------------------------------------------------------------------------
# Test specific imports
# --------------------------------------------------------------------------

import proteus.tests.fixtures as fixtures

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def create_unit_property_element(
    # Specific unit property attributes
    units: str,
    value: float,
    unit: str,
    # General property attributes
    name: str = DEFAULT_NAME,
    category: str = DEFAULT_CATEGORY,
    tooltip: str = str(),
    required: bool | str = False,
    inmutable: bool | str = False,
) -> ET._Element:
    """
    Create an unit property XML element with the given parameters.

    :param units: Space-separated list of units.
    :param value: Value of the measurement.
    :param unit: Unit of the measurement.
    :param name: Name of the property. Default is DEFAULT_NAME.
    :param category: Category of the property. Default is DEFAULT_CATEGORY.
    :param tooltip: Tooltip of the property. Default is empty string.
    :param required: Required attribute of the property. Default is False.
    :param inmutable: Inmutable attribute of the property. Default is False.
    :return: The created XML element.
    """
    unit_property_element: ET._Element = fixtures.create_property_element(
        property_tag=UNIT_PROPERTY_TAG,
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
    )

    if units:
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


@pytest.mark.parametrize(
    "units, expected_units",
    [
        ("years days hours", ["years", "days", "hours"]),
        (None, []),
    ],
)
def test_unit_property_factory(mocker, units, expected_units) -> None:
    """
    It tests the creation of a unit property from an XML element using the
    PropertyFactory. It is important to check every attribute of the unit
    property in order to ensure that the constructor is being called correctly.
    """
    # Arrange -------------------------
    name: str = "test_name"
    category: str = "test_category"
    value: float = 1.0
    unit: str = "years"
    tooltip: str = "test_tooltip"
    required: bool = True
    inmutable: bool = True

    # Mock the UnitProperty constructor in order to check its parameters
    mocker.patch(
        "proteus.model.properties.unit_property.UnitProperty.__init__",
        return_value=None,
    )

    expected_measurement: Measurement = Measurement(value=value, unit=unit)

    # Create XML element for unit property
    unit_property_element: ET._Element = create_unit_property_element(
        units,
        value,
        unit,
        name=name,
        category=category,
        tooltip=tooltip,
        required=required,
        inmutable=inmutable,
    )

    # Act -----------------------------
    # Create unit property from XML element
    PropertyFactory.create(unit_property_element)

    # Assert --------------------------
    # Check that the constructor was called with the expected parameters
    UnitProperty.__init__.assert_called_once_with(
        name,
        category,
        expected_measurement,
        tooltip,
        required,
        inmutable,
        expected_units,
    )


@pytest.mark.parametrize(
    "units, expected_units, expected_value, value, unit, expected_unit",
    [
        ("years days hours", ["years", "days", "hours"], 1.0, 1.0, "years", "years"),
        ("years", ["years"], 1.0, 1.0, "years", "years"),
        ("years", ["years"], 1.0, 1.0, "seconds", "years"),  # Unit is not in units
        ("years days", ["years", "days"], 1.0, 1.0, "seconds", "years"),
    ],
)
def test_unit_property_creation(
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
    ), f"Unit property units '{unit_property.units}' does not match expected units '{expected_units}'"

    assert (
        unit_property.value == expected_measurement
    ), f"Unit property value '{unit_property.value}' does not match expected value '{expected_measurement}'"


def test_unit_property_creation_unit_not_in_units() -> None:
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


def test_unit_property_creation_wrong_value_type() -> None:
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
    ), f"Generated XML element '{ET.tostring(generated_element)}' does not match expected XML element '{ET.tostring(unit_property_element)}"
