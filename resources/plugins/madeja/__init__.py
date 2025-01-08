# ==========================================================================
# Plugin: MADEJA
# Description: PROTEUS 'madeja' plugin for specific profile functionalities.
# Date: 03/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# NOTE: Functionalities that depends on projectOpenEvent may not work as expected
# when the project is opened at first. Due to the multithreading nature of the
# events, views and components are sometimes created before the plugin completes
# its process. This is critical for plugins that provides XSLT functions that
# depends on project data. This can be avoided if the state from state file
# is read because the current view is set again which forces XSLT reload.
# Possible solutions:
# - Force view reload after opening the project.

from madeja.glossary_handler import GlossaryHandler
from madeja.traceability_matrix_helper import TraceabilityMatrixHelper

def register(register_xslt_function, register_qwebchannel_class, register_proteus_component):

    # Glossary
    register_xslt_function("glossary_highlight", GlossaryHandler.highlight_glossary_items)
    register_proteus_component("glossaryHandler", GlossaryHandler)

    # Traceability Matrix
    register_proteus_component("traceabilityMatrixHelper", TraceabilityMatrixHelper, ["get_objects_from_classes", "check_dependency"])
