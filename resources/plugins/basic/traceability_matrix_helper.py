# ==========================================================================
# File: traceability_matrix_helper.py
# Description: Traceability matrix helper functions and classes
# Date: 07/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import List

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from lxml import etree as ET

# --------------------------------------------------------------------------
# Plugin imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Proteus imports
# --------------------------------------------------------------------------

from proteus.model import (
    ProteusID,
    PROTEUS_CODE,
    PROTEUS_NAME,
    PROTEUS_DEPENDENCY,
)
from proteus.model.object import Object
from proteus.model.properties.code_property import ProteusCode
from proteus.views.components.abstract_component import ProteusComponent


# Module configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: TraceabilityMatrixHelper
# Description: This class provides helper functions to work with the
#              traceability matrix.
# Date: 07/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
# TODO: Add cache capabilities to avoid innecesary calls to the controller
# when there is no objects changes.
class TraceabilityMatrixHelper(ProteusComponent):
    """
    Provides helper functions to work with the traceability matrix.

    The class provides two methods to be used in the traceability
    matrix XSLT file. The first one gets the objects from a list of classes
    and the second one checks if a dependency exists between two objects.
    """

    # --------------------------------------------------------------------------
    # Method: get_objects_from_classes
    # Description: This method (XSLT function) recieves a string with space-separated
    #              Proteus classes and return a node-set (List[_Element]) with the
    #              objects information that have the specified classes.
    # Date: 08/02/2024
    # Version: 0.2
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_objects_from_classes(self, context, classes: str) -> List[ET._Element]:
        """
        This method (XSLT function) recieves a string with space-separated
        Proteus classes and return a node-set (List[_Element]) with the objects
        information that have the specified classes.

        The selected object information is parsed in an specific XML format
        to make easier XSLT processing and improve readability.

        The object information retrieved is the Id and Code. If
        proteus code is not found, name is used instead.

        The XML format is the following:
            <object id="1234">
                <label>Object label</label>
            </object>

        :param context: The XSLT context (need to be present in the function signature)
        :param classes: A string with space-separated Proteus classes

        :return: A node-set (XPath object) with the objects information
        """
        classes = classes[0]

        # Objects -------------------------------------------------------------
        # Get the objects from the classes present in the project
        class_list: List[str] = classes.strip().split()
        objects: List[Object] = self._controller.get_objects(class_list)

        # Create ObjectMatrixInformation from objects and sort them by label
        objects_information: List[ObjectMatrixInformation] = []
        for obj in objects:
            obj_label: str

            # Try to get the proteus code, if not found, use the name
            code_prop = obj.get_property(PROTEUS_CODE)
            if code_prop is not None:
                code: ProteusCode = code_prop.value
                obj_label = code.to_string()
            else:
                obj_label = obj.get_property(PROTEUS_NAME).value

            # Create the object information item and add it to the list
            objects_information.append(ObjectMatrixInformation(obj.id, obj_label))

        # Sort the objects by label
        objects_information.sort(key=lambda obj: obj.label)

        # Node-set ------------------------------------------------------------
        node_set: List[ET._Element] = []

        # Add the object information to the root element
        for obj_info in objects_information:
            node = obj_info.generate_node()
            node_set.append(node)

        return node_set

    # --------------------------------------------------------------------------
    # Method: check_dependency
    # Description: This method (XSLT function) checks if a dependency exists between
    #              two objects.
    # Date: 08/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def check_dependency(
        self, context, source_id: ProteusID, target_id: ProteusID
    ) -> str:
        """
        This method (XSLT function) checks if a dependency exists between
        two objects.

        :param context: The XSLT context (no need to be present in the function signature)
        :param source_id: The id of the source object
        :param target_id: The id of the target object

        :return: True if a dependency exists, False otherwise. The result is
                 returned as string to be used in the XSLT file.
        """
        source_id = source_id[0]
        target_id = target_id[0]

        # Get the source and target objects
        try:
            source_obj: Object = self._controller.get_element(source_id)
            self._controller.get_element(
                target_id
            )  # Check existence

        # If an error occurs, return False
        except Exception as e:
            log.error(f"Error while trying to get the source and target objects: {e}")
            return str(False)

        # Get source traces
        source_traces = source_obj.get_traces()
        for trace in source_traces:
            # Check if the trace is a dependency type
            if trace.traceType == PROTEUS_DEPENDENCY:
                # Check if the target object is the target of the dependency
                if target_id in trace.value:
                    return str(True)

        return str(False)


# --------------------------------------------------------------------------
# Class: ObjectMatrixInformation
# Description: This class represents the information of an object in the
#              traceability matrix.
# Date: 07/02/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ObjectMatrixInformation:
    """
    Class that represents the basic information of an object in the
    traceability matrix. It generates the node (etree.Element) with the
    object information in a specific XML format to make easier XSLT
    processing.

    The object information retrieved is the Id and matrix label.
    """

    def __init__(self, id: ProteusID, label: str):
        self.id = id
        self.label = label

    def generate_node(self) -> ET._Element:
        """
        Get the XML representation of the object information
        """
        element = ET.Element("object", id=self.id)
        label = ET.SubElement(element, "label")
        label.text = self.label
        return element
