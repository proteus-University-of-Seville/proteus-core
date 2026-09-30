# ==========================================================================
# File: test_property_input.py
# Description: pytest file for the PROTEUS property input
# Date: 27/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QLineEdit, QMessageBox

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import PROTEUS_NAME
from proteus.model.properties import (
    StringProperty,
    MarkdownProperty,
    IntegerProperty,
    FloatProperty,
    UrlProperty,
    Property,
    CodeProperty,
)
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.properties.property_input_factory import PropertyInputFactory
from proteus.views.forms.markdown_edit import MarkdownEdit
from proteus.views.forms.code_edit import CodeEdit
from proteus.views.components.dialogs.base_dialogs import MessageBox

from proteus.tests.end2end.fixtures import get_dialog


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def create_property(
    property_class,
    name="",
    value="",
    category="",
    required=False,
    inmutable=False,
    tooltip="",
) -> Property:
    return property_class(
        name=str(name),
        value=str(value),
        required=required,
        inmutable=inmutable,
        category=str(category),
        tooltip=str(tooltip),
    )


# --------------------------------------------------------------------------
# Inmutable checkbox tests
# --------------------------------------------------------------------------
def test_inmutable_checkbox_creation(qtbot: QtBot):
    """
    Test inmutable checkbox is created and checked when the property is inmutable.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(StringProperty, inmutable=True)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    inmutable_checkbox = property_input.inmutable_checkbox

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    assert inmutable_checkbox is not None, "Inmutable checkbox was not created"
    assert (
        inmutable_checkbox.isChecked() == True
    ), "Inmutable checkbox was not checked as expected"


def test_inmutable_checkbox_not_creation(qtbot: QtBot):
    """
    Test inmutable checkbox is not created and checked when the property is not inmutable.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(StringProperty, inmutable=False)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    inmutable_checkbox = property_input.inmutable_checkbox

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    assert inmutable_checkbox is None, "Inmutable checkbox was created"


def test_inmutable_checkbox_click(qtbot: QtBot, mocker):
    """
    Test inmutable checkbox click event triggers setEnabled() method in the input widget
    and message box dialog is shown.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(StringProperty, inmutable=True)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    inmutable_checkbox = property_input.inmutable_checkbox

    mocker.patch.object(property_input.input, "setEnabled")

    # --------------------------------------------
    # Act
    # --------------------------------------------
    message_box: MessageBox = get_dialog(inmutable_checkbox.click)
    message_box.button(QMessageBox.StandardButton.Ok).click()

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    assert (
        inmutable_checkbox.isChecked() == False
    ), "Inmutable checkbox was not unchecked as expected"

    property_input.input.setEnabled.assert_called_once_with(True)

# --------------------------------------------------------------------------
# Validation tests
# --------------------------------------------------------------------------


def test_string_property_proteus_name_validation(qtbot: QtBot):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(StringProperty, name=PROTEUS_NAME)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: QLineEdit = property_input.input
    input_widget.setText("")

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    expected_error = "property_input.validator.error.required"
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but none was found"


@pytest.mark.parametrize(
    "property_value, required, expected_error",
    [
        ("test", True, None),
        ("", True, "property_input.validator.error.required"),
        (None, True, "property_input.validator.error.required"),
        ("]]>", False, "string_property_input.validator.error.cdata"),
        ("<![CDATA[", False, "string_property_input.validator.error.cdata"),
        (
            "<![CDATA[dummy cdata]]>",
            False,
            "string_property_input.validator.error.cdata",
        ),
    ],
)
def test_string_property_validation(qtbot: QtBot, property_value, required, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(StringProperty, required=required)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: QLineEdit = property_input.input
    input_widget.setText(property_value)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


@pytest.mark.parametrize(
    "property_value, required, expected_error",
    [
        ("test", True, None),
        ("", True, "property_input.validator.error.required"),
        (None, True, "property_input.validator.error.required"),
        ("]]>", False, "markdown_property_input.validator.error.cdata"),
        ("<![CDATA[", False, "markdown_property_input.validator.error.cdata"),
        (
            "<![CDATA[dummy cdata]]>",
            False,
            "markdown_property_input.validator.error.cdata",
        ),
    ],
)
def test_markdown_property_validation(qtbot: QtBot, property_value, required, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(MarkdownProperty, required=required)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: MarkdownEdit = property_input.input
    input_widget.setMarkdown(property_value)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


# FloatProperty cannot be set to None/empty, it will always be 0.0 if not valid
# so the required validation is not necessary (27/02/2024)
@pytest.mark.parametrize(
    "property_value, expected_error",
    [
        ("1.0", None),
        ("", "float_property_input.validator.error"),
        (None, "float_property_input.validator.error"),
        ("a", "float_property_input.validator.error"),
        ("1.2.3", "float_property_input.validator.error"),
        ("1.2a", "float_property_input.validator.error"),
    ],
)
def test_float_property_validation(qtbot: QtBot, property_value, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(FloatProperty)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: QLineEdit = property_input.input
    input_widget.setText(property_value)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


# IntegerProperty cannot be set to None/empty, it will always be 0 if not valid
# so the required validation is not necessary (27/02/2024)
@pytest.mark.parametrize(
    "property_value, expected_error",
    [
        ("1", None),
        ("", "integer_property_input.validator.error"),
        (None, "integer_property_input.validator.error"),
        ("a", "integer_property_input.validator.error"),
        ("1.2", "integer_property_input.validator.error"),
        ("1a", "integer_property_input.validator.error"),
    ],
)
def test_integer_property_validation(qtbot: QtBot, property_value, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(IntegerProperty)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: QLineEdit = property_input.input
    input_widget.setText(property_value)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


@pytest.mark.parametrize(
    "property_value, required, expected_error",
    [
        ("test", True, None),
        ("", True, "property_input.validator.error.required"),
        (None, True, "property_input.validator.error.required"),
        ("]]>", False, "url_property_input.validator.error.cdata"),
        ("<![CDATA[", False, "url_property_input.validator.error.cdata"),
        ("https://url.url/]]>/", False, "url_property_input.validator.error.cdata"),
    ],
)
def test_url_property_validation(qtbot: QtBot, property_value, required, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(UrlProperty, required=required)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: QLineEdit = property_input.input
    input_widget.setText(property_value)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


# CodeProperty prefix and number cannot be set to None/Empty,
# so the required validation is not necessary (27/02/2024)
@pytest.mark.parametrize(
    "prefix, number, suffix, expected_error",
    [
        ("", "1", "", "code_property_input.validator.error.prefix"),
        (
            "prefix",
            "",
            "",
            "code_property_input.validator.error.number_type",
        ),  # integer validation
        ("prefix", "a", "", "code_property_input.validator.error.number_type"),
        ("prefix", "1.2", "", "code_property_input.validator.error.number_type"),
        (
            "prefix",
            "-1",
            "",
            "code_property_input.validator.error.number_value",
        ),  # positive number validation
        ("prefix", "0", "", "code_property_input.validator.error.number_value"),
        (
            "prefix",
            "1",
            "]]>",
            "code_property_input.validator.error.cdata",
        ),  # suffix cdata
        ("prefix", "1", "<![CDATA[", "code_property_input.validator.error.cdata"),
        (
            "prefix",
            "1",
            "<![CDATA[dummy cdata]]>",
            "code_property_input.validator.error.cdata",
        ),
        ("]]>", "1", "", "code_property_input.validator.error.cdata"),  # prefix cdata
        ("<![CDATA[", "1", "", "code_property_input.validator.error.cdata"),
        (
            "<![CDATA[dummy cdata]]>",
            "1",
            "",
            "code_property_input.validator.error.cdata",
        ),
    ],
)
def test_code_property_validation(qtbot: QtBot, prefix, number, suffix, expected_error):
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    property: Property = create_property(CodeProperty)
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    input_widget: CodeEdit = property_input.input
    input_widget.setCode(prefix, number, suffix)

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    current_error = property_input.validate()
    assert (
        current_error == expected_error
    ), f"Error '{expected_error}' was expected but '{current_error}' was found"


def test_unit_property_returns_unit_key_with_translated_units(qtbot: QtBot, mocker):
    """
    The unit combo box shows translated unit labels, but the property value
    must keep the unit key (e.g. 'day', not 'día'). Otherwise the unit is
    not found in the units list and silently replaced by the first one.
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    from proteus.model.properties.unit_property import UnitProperty, Measurement

    # Translate every unit to a different label
    mocker.patch(
        "proteus.views.forms.measurement_edit._",
        side_effect=lambda key, alternative_text=None: f"translated-{alternative_text}",
    )
    property = UnitProperty(
        name="frequency",
        units=["year", "day", "hour"],
        value=Measurement(value=10, unit="day"),
    )
    property_input: PropertyInput = PropertyInputFactory.create(property)

    # --------------------------------------------
    # Act
    # --------------------------------------------
    combo = property_input.input.unit_combo
    shown_unit = combo.currentText()
    combo.setCurrentIndex(combo.findData("hour"))
    value = property_input.get_value()

    # --------------------------------------------
    # Assert
    # --------------------------------------------
    assert shown_unit == "translated-day", f"Unexpected combo label '{shown_unit}'"
    assert value == Measurement(
        value=10, unit="hour"
    ), f"Expected 10 hour, got {value.value} {value.unit}"
