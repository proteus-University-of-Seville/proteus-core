# ==========================================================================
# File: impact_analyzer.py
# Description: PyQT6 impact analysis class
# Date: 21/11/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import List, Set

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Plugin imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Proteus imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.model.abstract_object import ProteusState
from proteus.model.object import Object
from proteus.views.components.abstract_component import ProteusComponent


# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ImpactAnalyzer
# Description: Impact analyzer class
# Date: 22/12/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ImpactAnalyzer(ProteusComponent):

    # --------------------------------------------------------------------------
    # Method: calculate_affected_objects
    # Description: Calculate the affected objects from a given object
    # Date: 22/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def calculate_affected_objects(
        self,
        analyzed_object: ProteusID,
        trace_types: List[str],
        affected_objects: Set[Object] = set(),
    ) -> Set[Object]:
        """
        Calculate the affected objects in case of a change in the analyzed object.
        It only considers provided trace types.

        :param ProteusID analyzed_object: ID of the object to analyze
        :param List[str] trace_types: list of trace types to consider
        :param Set[Object] affected_objects: set of already affected objects, defaults to set()
        :return Set[Object]: set of affected objects
        """

        object_pointers = self._controller.get_objects_pointing_to(analyzed_object)
        for object_id, trace_type in object_pointers:

            if object_id in [obj.id for obj in affected_objects]:
                continue

            object = self._controller.get_element(object_id)

            if object.state == ProteusState.DEAD:
                continue

            if trace_type in trace_types:
                affected_objects.add(object)
                new_affected_objects = self.calculate_affected_objects(
                    object.id, trace_types, affected_objects.copy()
                )

                affected_objects.update(new_affected_objects)

        return affected_objects

    # --------------------------------------------------------------------------
    # Method: calculate_impact
    # Description: Calculate the impact of a set of objects and return the affected
    #              objects ids
    # Date: 25/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def calculate_impact(
        self, analyzed_objects_ids: List[ProteusID], trace_types: List[str]
    ) -> List[ProteusID]:
        """
        Calculate the impact of a set of objects and return the affected objects ids.
        Do not consider the analyzed objects in the result.

        :param analyzed_objects_ids: The ids of the objects to analyze
        :param trace_types: The types of traces to consider
        :return List[ProteusID]: The ids of the affected objects
        """
        # Calculate the affected objects
        affected_objects: Set[Object] = set()
        for analyzed_object_id in analyzed_objects_ids:
            analyzed_object: Object = self._controller.get_element(analyzed_object_id)
            _affected_objects = self.calculate_affected_objects(
                analyzed_object_id, trace_types, set([analyzed_object])
            )
            affected_objects.update(_affected_objects)

        # Return the affected objects ids that are not in the analyzed objects
        return [
            obj.id for obj in affected_objects if obj.id not in analyzed_objects_ids
        ]

    # =========================================================================
    # XSLT methods
    # =========================================================================

    # --------------------------------------------------------------------------
    # Method: _calculate_impact
    # Description: Calculate the impact of a set of objects and return the affected
    #              objects ids. Do not consider the analyzed objects in the result.
    # Date: 25/12/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _calculate_impact(
        self, context, analyzed_objects_ids: list[str], trace_types: list[str]
    ) -> List[ProteusID]:
        """
        Calculate the impact of a set of objects and return the affected objects ids.
        Do not consider the analyzed objects in the result.

        :param context: The XSLT context (no need to be present in the function signature)
        :param analyzed_objects_ids: The ids of the objects to analyze (separated by spaces)
        :param trace_types: The types of traces to consider (separated by spaces)
        :return List[ProteusID]: The ids of the (indirectly) affected objects
        """

        # Parse input parameters (make sure list are not empty)
        if len(analyzed_objects_ids) == 1:
            analyzed_objects_ids: List[ProteusID] = analyzed_objects_ids[0].split()
        if len(trace_types) == 1:
            trace_types: List[str] = trace_types[0].split()

        # Calculate the affected objects
        result = self.calculate_impact(analyzed_objects_ids, trace_types)
        return result
