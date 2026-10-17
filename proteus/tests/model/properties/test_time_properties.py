# ==========================================================================
# File: test_time_properties.py
# Description: pytest file for PROTEUS time properties
# Date: 22/10/2022
# Version: 0.3
# Author: Pablo Rivera Jiménez
#         Amador Durán Toro
# ==========================================================================
# Update: 21/10/2022 (Amador)
# Description:
# - Code review.
# - Use of datetime substraction to count difference in seconds.
# - epsilon set to 10 seconds.
# ==========================================================================
# Update: 22/10/2022 (Amador)
# Description:
# - Common code extracted as fixtures.
# - epsilon set to 5 seconds.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import datetime

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties import TIME_PROPERTY_TAG, TIME_FORMAT

# --------------------------------------------------------------------------
# Test specific imports
# --------------------------------------------------------------------------

import proteus.tests.fixtures as fixtures

# --------------------------------------------------------------------------
# Time property tests
# --------------------------------------------------------------------------

# Expected value of an invalid time: the current time, which has to be
# calculated when the test runs, not when the tests are collected (the whole
# suite may take longer than the tolerance)
NOW = 'now'


def expected_time_as_string(expected: str) -> str:
    """
    The given expected time, or the current time if it is NOW.
    """
    if expected == NOW:
        return datetime.datetime.now().time().strftime(TIME_FORMAT)
    return expected


@pytest.mark.parametrize('name',         [str(), 'test name'     ])
@pytest.mark.parametrize('category',     [str(), 'test category' ])
@pytest.mark.parametrize('value, expected_value', 
    [
        ('20:10:02', '20:10:02'),
        (str(),        NOW),
        ('26:10:02',   NOW),
        ('20:61:02',   NOW),
        ('20:10:99',   NOW),
        ('not a time', NOW)
    ]
)
@pytest.mark.parametrize('new_value, expected_new_value',
    [
        ('20:10:02', '20:10:02'),
        (str(),        NOW),
        ('26:10:02',   NOW),
        ('20:61:02',   NOW),
        ('20:10:99',   NOW),
        ('not a time', NOW)
    ]
)

def test_time_properties(name, category, value, expected_value, new_value, expected_new_value):
    """
    It tests creation, update, and evolution (cloning with a new value) 
    of time properties.
    """
    # Create property from XML element
    property_tag = TIME_PROPERTY_TAG
    expected_value = expected_time_as_string(expected_value)
    (property, name, category) = fixtures.create_property(property_tag, name, category, value)

    # Create a time from the expected_value string
    # This could be avoided passing times as expected value
    expected_value_as_time = datetime.datetime.strptime(expected_value, TIME_FORMAT).time()

    # Maximum number of seconds between the calculation of the expected time and
    # the creation of the property (both in this test)
    epsilon_seconds = 10

    # To calculate the difference between two times, they have to be converted into datetime
    # https://stackoverflow.com/questions/43305577/python-calculate-the-difference-between-two-datetime-time-objects
    delta = \
        datetime.datetime.combine(datetime.date.today(), property.value) - \
        datetime.datetime.combine(datetime.date.today(), expected_value_as_time)        
    
    # Check property
    assert(property.name == name)
    assert(property.category == category)    
    assert(delta.total_seconds() < epsilon_seconds)

    # To avoid fail because of potentional difference in seconds, we just check
    # that the property value is correctly generated in XML.
    assert(
        ET.tostring(property.generate_xml()).decode() ==
        f'<{property_tag} name="{name}" category="{category}">{property.value.strftime(TIME_FORMAT)}</{property_tag}>'
    )

    # Clone the property without changes
    # Suprinsingly, clone() produces small differences in miliseconds
    cloned_property = property.clone()

    # To calculate the difference between two times, they have to be converted into datetime
    delta = \
        datetime.datetime.combine(datetime.date.today(), property.value) - \
        datetime.datetime.combine(datetime.date.today(), cloned_property.value)

    # Check cloned property
    assert(cloned_property.name == property.name)
    assert(cloned_property.category == property.category)
    assert(delta.total_seconds() < epsilon_seconds)    

    # Clone the property changing value
    expected_new_value = expected_time_as_string(expected_new_value)
    evolved_property = property.clone(str(new_value))

    # Create a time from the expected_new_value string    
    expected_new_value_as_time = datetime.datetime.strptime(expected_new_value, TIME_FORMAT).time()

    # To calculate the difference between two times, they have to be converted into datetime
    delta = \
        datetime.datetime.combine(datetime.date.today(), evolved_property.value) - \
        datetime.datetime.combine(datetime.date.today(), expected_new_value_as_time)        

    # Check cloned property
    assert(evolved_property.name == name)
    assert(evolved_property.category == category)
    assert(delta.total_seconds() < epsilon_seconds)  

    # To avoid fail because of potentional difference in seconds, we just check
    # that the property value is correctly generated in XML.
    assert(
        ET.tostring(evolved_property.generate_xml()).decode() ==
        f'<{property_tag} name="{name}" category="{category}">{evolved_property.value.strftime(TIME_FORMAT)}</{property_tag}>'
    )

