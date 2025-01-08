# ==========================================================================
# File: abstract_object.py
# Description: a PROTEUS abstract class to be used as a superclass for both
# projects and objects
# Date: 15/09/2022
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================
# Update: 26/09/2022 (Amador)
# Description:
# - Using get in dictionaries to return None if key is not found. Using
#   square brackets throw an exception if the key does not exits.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from enum import Enum
from typing import Type, List, Set
from abc import ABC, abstractmethod

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports (starting from root)
# --------------------------------------------------------------------------

from proteus.model import (
    ProteusID,
    NAME_ATTRIBUTE,
    PROPERTIES_TAG,
)
from proteus.model.properties import Property, PropertyFactory


# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Class: ProteusStates
# Description: Enumeration for abstract object's state
# Date: 17/09/2022
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


class ProteusState(Enum):
    """
    Enumeration for abstract object's state.
    """

    FRESH = 0  # new object, just cloned but not already saved
    CLEAN = 1  # loaded object, not modified
    DIRTY = 2  # loaded object, modified
    DEAD = 3  # loaded object, to be deleted


# --------------------------------------------------------------------------
# Class: AbstractObject
# Description: Abstract base class (ABC) to be used as a superclass for both
# projects and objects (they are very similar)
# Date: 15/09/2022
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------


class AbstractObject(ABC):
    """
    A PROTEUS abstract object is an abstraction of PROTEUS projects and
    objects. It contains all features which are common to both types of
    PROTEUS objects, especially, their path to its XML file, its ID, and
    its properties (and probably more in the future).
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: It initializes a PROTEUS abstract project.
    # Date       : 26/09/2022
    # Version    : 0.2 (path assert simplified)
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------

    def __init__(self, path) -> None:
        """
        It initializes an abstract PROTEUS object.

        :param path: the path to the XML file containing the object's data.
        """

        # TODO: put all common code in Project and Object here

        # path to XML file (to be initialized in other methods?)
        self.path: str = path

        # short UUID (to be initialized in other methods?)
        self.id: ProteusID = None

        # state (to be initialized in other methods?)
        self.state: ProteusState = ProteusState.CLEAN

        # Properties dictionary (indexed by property names)
        self.properties: dict[str, Property] = dict[str, Property]()

    # ----------------------------------------------------------------------
    # Method     : load_properties
    # Description: It loads the properties of a PROTEUS abstract object.
    # Date       : 26/09/2022 (using get with None as default value)
    # Version    : 0.3
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------

    def load_properties(self, root: ET._Element) -> None:
        """
        It loads a PROTEUS abstract object's properties from an XML root element.

        :param root: the XML root element.
        :type root: ET._Element
        """

        # Check root is not None
        assert root is not None, f"Root element is not valid in {self.path}."

        # Find the <properties> element
        properties_element: ET._Element = root.find(PROPERTIES_TAG)

        # Check whether it has <properties>
        assert (
            properties_element is not None
        ), f"PROTEUS file {self.path} does not have a <{PROPERTIES_TAG}> element."

        # Parse properties
        property_element: ET._Element
        for property_element in properties_element:
            property_name: str = property_element.attrib.get(NAME_ATTRIBUTE, None)
            # Check whether the property has a name
            assert (
                property_name is not None
            ), f"PROTEUS file {self.path} includes an unnamed property."

            # Add the property to the properties dictionary
            property: Property = PropertyFactory.create(property_element)
            if property is not None:
                self.properties[property_name] = property
            else:
                log.error(
                    f"Property {property_name} could not be created from {self.path}."
                )

    # ----------------------------------------------------------------------
    # Method     : get_property
    # Description: It returns an object's property given its name.
    # Date       : 17/09/2022
    # Version    : 0.2
    # Author     : Pablo Rivera Jiménez
    #              Amador Durán Toro
    # ----------------------------------------------------------------------

    def get_property(self, key: str) -> Property | None:
        """
        It returns an object's property given its name.
        If property is not found by name, it returns None.

        :param key: the name of the property to be returned.
        :return: the property with the given name.
        """
        return self.properties.get(key, None)

    # ----------------------------------------------------------------------
    # Method     : set_property
    # Description: It sets an object's property.
    # Date       : 17/09/2022
    # Version    : 0.2
    # Author     : Pablo Rivera Jiménez
    #              Amador Durán Toro
    # ----------------------------------------------------------------------

    def set_property(self, new_property: Property) -> None:
        """
        It sets an abstract object's (Object and Project) property.

        :param new_property: the new property to be set.
        :type new_property: Property
        """

        # Get new property name
        new_property_name: str = new_property.name

        # Get current property with that name (or None)
        current_property: Property = self.properties.get(new_property_name, None)

        # Check current property exists
        assert (
            current_property is not None
        ), f"Cannot set nonexistent property {new_property_name} in {self.id} properties"

        # Get current property concrete class
        current_property_class: Type = current_property.__class__

        # Get new property concrete class
        new_property_class: Type = new_property.__class__

        # Check current and new properties are instances of the same class
        assert (
            current_property_class == new_property_class
        ), f"Current and new property types are different in {self.id}: {current_property_class} != {new_property_class}"

        # Update property
        self.properties[new_property_name] = new_property

        # Update object's state
        if self.state == ProteusState.CLEAN:
            self.state = ProteusState.DIRTY

    # ----------------------------------------------------------------------
    # Method     : generate_properties_xml
    # Description: method for generating an XML element from the properties
    # of an abstract object.
    # Date       : 15/09/2022
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------

    def generate_xml_properties(self, parent_element: ET._Element) -> ET._Element:
        """
        Generate xml property function. It generates an ET.Element from the properties of an abstract object
        (Object and Project).

        :param parent_element: ET.Element. The parent element of the properties.
        :return: ET.Element. The properties element.
        """

        # Check parent element is not None
        assert (
            parent_element is not None
        ), f"Properties cannot be generated for a null parent element. {self.uuid=}"

        # Create <properties> element
        properties_element = ET.SubElement(parent_element, PROPERTIES_TAG)

        # Create <property> subelements
        for property in self.properties.values():
            properties_element.append(property.generate_xml())

        # return parent elmenent, i.e. <project> or <object>
        return parent_element

    # ----------------------------------------------------------------------
    # Method     : get_ids
    # Description: It returns a set with all the ids of the project
    # Date       : 23/05/2023
    # Version    : 0.2
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------

    def get_ids(self) -> Set[ProteusID]:
        """
        Method that returns a set with all the ids of the descendants recursively.

        :return: A set with all the ids of the object including its children recursively.
        """

        # Initialize an empty set of ids
        ids: Set[ProteusID] = set()

        # For each object in the project or object, we get the ids of the objects
        # and their children recursively
        descendant: AbstractObject
        for descendant in self.get_descendants():
            ids.update(descendant.get_ids())

        ids.add(self.id)

        return ids

    # ----------------------------------------------------------------------
    # Method     : get_descendants_recursively
    # Description: It returns a list with all the descendants of an object
    # including the object itself.
    # Date       : 29/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_descendants_recursively(
        self, ignore_dead_children: bool = False
    ) -> Set["AbstractObject"]:
        """
        It returns a list with all the descendants of an object/project including itself.

        :param ignore_dead_children: If True, dead children branches are not included in the set.
        :return: Set with all the descendants of an object/project including itself.
        """
        descendants = set()
        descendants.add(self)
        for child in self.get_descendants():
            if ignore_dead_children and child.state == ProteusState.DEAD:
                continue

            descendants.update(
                child.get_descendants_recursively(
                    ignore_dead_children=ignore_dead_children
                )
            )
        return descendants

    # ----------------------------------------------------------------------
    # Method     : get_descendants
    # Description: It returns a list with all the descendants of an object.
    # Date       : 23/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @abstractmethod
    def get_descendants(self) -> List["AbstractObject"]:
        """
        It returns a list with all the descendants of an object.

        :return: a list with all the descendants of an object.
        """
        pass

    # ----------------------------------------------------------------------
    # Method     : add_descendant
    # Description: It adds a descendant to a PROTEUS abstract object.
    # Date       : 26/04/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @abstractmethod
    def add_descendant(self, child, position: int = None) -> None:
        """
        It adds a descendant to a PROTEUS abstract object.

        :param child: the descendant to be added.
        :param position: the position where the descendant is added.
        """
        pass

    # ----------------------------------------------------------------------
    # Method     : accept_descendant
    # Description: It checks if a descendant can be added to a PROTEUS
    # abstract object.
    # Date       : 09/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @abstractmethod
    def accept_descendant(self, child) -> bool:
        """
        It checks if a descendant can be added to a PROTEUS abstract object.

        :param child: the descendant to be added.
        :return: True if the descendant can be added, False otherwise.
        """
        pass
