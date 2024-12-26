# ==========================================================================
# File: property_factory.py
# Description: PROTEUS property Factory
# Date: 27/02/2023
# Version: 0.3
# Author: Amador Durán Toro
#         Pablo Rivera Jiménez
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_ANY
from proteus.model import ProteusClassTag
from proteus.model.properties.property import Property
from proteus.model.properties.string_property import StringProperty
from proteus.model.properties.boolean_property import BooleanProperty
from proteus.model.properties.date_property import DateProperty
from proteus.model.properties.time_property import TimeProperty
from proteus.model.properties.markdown_property import MarkdownProperty
from proteus.model.properties.integer_property import IntegerProperty
from proteus.model.properties.float_property import FloatProperty
from proteus.model.properties.enum_property import EnumProperty
from proteus.model.properties.file_property import FileProperty
from proteus.model.properties.url_property import UrlProperty
from proteus.model.properties.classlist_property import ClassListProperty
from proteus.model.properties.trace_property import TraceProperty
from proteus.model.properties.code_property import CodeProperty, ProteusCode
from proteus.model.properties.tracetypelist_property import TraceTypeListProperty
from proteus.model.properties.unit_property import UnitProperty, Measurement

from proteus.model import (
    NAME_ATTRIBUTE,
    CATEGORY_ATTRIBUTE,
    REQUIRED_ATTRIBUTE,
    INMUTABLE_ATTRIBUTE,
    TOOLTIP_ATTRIBUTE,
    TARGET_ATTRIBUTE,
    TRACE_TYPE_ATTRIBUTE,
    ACCEPTED_TARGETS_ATTRIBUTE,
    EXCLUDED_TARGETS_ATTRIBUTE,
    MAX_TARGETS_NUMBER_ATTRIBUTE,
    CHOICES_ATTRIBUTE,
    VALUE_TOOLTIPS_ATTRIBUTE,
    UNITS_ATTRIBUTE,
)

from proteus.model.properties import (
    CLASS_TAG,
    PREFIX_TAG,
    NUMBER_TAG,
    SUFFIX_TAG,
    TRACE_TAG,
    TYPE_TAG,
    NO_TARGETS_LIMIT,
    DEFAULT_TRACE_TYPE,
    VALUE_TAG,
    UNIT_TAG,
)

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: PropertyFactory
# Description: Factory class for PROTEUS properties
# Date: 30/08/2022
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


class PropertyFactory:
    """
    Factory class for PROTEUS properties.
    """

    # Dictionary of valid property types and classes (class attribute)
    # Note the type hint type[Property] for the dictionary
    # https://adamj.eu/tech/2021/05/16/python-type-hints-return-class-not-instance/
    propertyFactory: dict[str, type[Property]] = {
        BooleanProperty.element_tagname: BooleanProperty,
        StringProperty.element_tagname: StringProperty,
        DateProperty.element_tagname: DateProperty,
        TimeProperty.element_tagname: TimeProperty,
        MarkdownProperty.element_tagname: MarkdownProperty,
        IntegerProperty.element_tagname: IntegerProperty,
        FloatProperty.element_tagname: FloatProperty,
        EnumProperty.element_tagname: EnumProperty,
        FileProperty.element_tagname: FileProperty,
        UrlProperty.element_tagname: UrlProperty,
        ClassListProperty.element_tagname: ClassListProperty,
        CodeProperty.element_tagname: CodeProperty,
        TraceProperty.element_tagname: TraceProperty,
        TraceTypeListProperty.element_tagname: TraceTypeListProperty,
        UnitProperty.element_tagname: UnitProperty,
    }

    @classmethod
    def create(cls, element: ET._Element) -> Property | None:
        """
        Factory class method for PROTEUS properties.
        :param element: XML element with the property.
        :return: Property object or None if the property type is not valid.
        """
        # Check it is one of the valid property types -------------------------
        try:
            property_class = cls.propertyFactory[element.tag]
        except KeyError:
            log.warning(
                f"<{element.tag}> is not a valid PROTEUS property type -> ignoring invalid property"
            )
            return None

        # General attributes --------------------------------------------------

        # Get name (checked in property constructors)
        name = element.attrib.get(NAME_ATTRIBUTE)

        # Get category (checked in property constructors)
        category = element.attrib.get(CATEGORY_ATTRIBUTE)

        # Get required (checked in property constructors)
        required_str = element.attrib.get(REQUIRED_ATTRIBUTE, "false")
        required: bool = True if required_str.lower() == "true" else False

        # Get inmutable (checked in property constructors)
        inmutable_str = element.attrib.get(INMUTABLE_ATTRIBUTE, "false")
        inmutable: bool = True if inmutable_str.lower() == "true" else False

        # Get tooltip (checked in property constructors)
        tooltip = element.attrib.get(TOOLTIP_ATTRIBUTE, str())

        # Specific attributes handling ----------------------------------------

        # Get value (checked in property constructors)
        if property_class is ClassListProperty:
            # We need to collect the list of class names,
            # put them toghether in a list of ProteusClassTag objects
            if element.findall(CLASS_TAG):
                value = [ProteusClassTag(e.text) for e in element.findall(CLASS_TAG)]
            else:
                value = list()
        elif property_class is TraceTypeListProperty:
            # We need to collect the list of trace type names
            if element.findall(TYPE_TAG):
                value = [e.text for e in element.findall(TYPE_TAG)]
            else:
                value = list()
        elif property_class is CodeProperty:
            # We need to collect its prefix, number and suffix
            prefix = element.find(PREFIX_TAG).text
            number = element.find(NUMBER_TAG).text
            suffix = element.find(SUFFIX_TAG).text
            value = ProteusCode(prefix, number, suffix)
        elif property_class is TraceProperty:
            traces = list()

            for trace in element.findall(TRACE_TAG):
                target: ProteusID = trace.attrib.get(TARGET_ATTRIBUTE)

                if target is None:
                    log.warning(
                        f"PROTEUS trace '{name}' has a trace without a target -> ignoring it"
                    )
                    continue

                traces.append(target)

            value = traces
        elif property_class is UnitProperty:
            # We need to collect its value and unit
            value = Measurement(
                float(element.find(VALUE_TAG).text),
                element.find(UNIT_TAG).text,
            )
        else:
            # Value could be empty
            value = str(element.text)

        # Create and return the property object -------------------------------

        # Special case: EnumProperty
        if property_class is EnumProperty:
            # We need to collect its choices
            choices = element.attrib.get(CHOICES_ATTRIBUTE, str())

            # We need to collect valueTooltips attribute
            value_tooltips_str = element.attrib.get(VALUE_TOOLTIPS_ATTRIBUTE, "false")
            value_tooltips: bool = (
                True if value_tooltips_str.lower() == "true" else False
            )

            return EnumProperty(
                name,
                category,
                value,
                tooltip,
                required,
                inmutable,
                value_tooltips,
                choices,
            )

        # Special case: traceProperty
        elif property_class is TraceProperty:
            # We need to collect its trace type, max targets number and accepted targets
            trace_type = element.attrib.get(TRACE_TYPE_ATTRIBUTE, DEFAULT_TRACE_TYPE)

            accepted_targets: List = element.attrib.get(
                ACCEPTED_TARGETS_ATTRIBUTE, PROTEUS_ANY
            ).split()

            excluded_targets: List = element.attrib.get(
                EXCLUDED_TARGETS_ATTRIBUTE, ""
            ).split()

            try:
                max_targets_number: int = int(
                    element.attrib.get(MAX_TARGETS_NUMBER_ATTRIBUTE, NO_TARGETS_LIMIT)
                )
            except ValueError:
                log.warning(
                    f"PROTEUS propertyTrace '{name}' has a max targets number that is not an integer -> assigning NO_TARGETS_LIMIT=-1 as max targets number"
                )
                max_targets_number = NO_TARGETS_LIMIT

            return TraceProperty(
                name,
                category,
                value,
                tooltip,
                required,
                inmutable,
                accepted_targets,
                excluded_targets,
                trace_type,
                max_targets_number,
            )

        # Special case: UnitProperty
        elif property_class is UnitProperty:
            units_str = element.attrib.get(UNITS_ATTRIBUTE, str())
            units = units_str.split()
            return UnitProperty(
                name, category, value, tooltip, required, inmutable, units
            )
        else:
            # Ordinary case: rest of property classes
            return property_class(name, category, value, tooltip, required, inmutable)
