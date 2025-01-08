# ==========================================================================
# Plugin: basics
# Description: PROTEUS 'basics' plugin provides general XSLT utilities and
#              QWebChannel classes for PROTEUS.
# Date: 06/03/2024
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

from basics.proteus_xslt_basics import generate_markdown, image_to_base64, current_document
from basics.proteus_xslt_basics import ProteusBasicMethods
from basics.document_interactions import DocumentInteractions
from basics.impact_analyzer import ImpactAnalyzer


def register(register_xslt_function, register_qwebchannel_class, register_proteus_component):

    # Document Interactions
    register_qwebchannel_class("documentInteractions", DocumentInteractions)

    # Impact analyzer
    register_proteus_component("impactAnalyzer", ImpactAnalyzer, ["_calculate_impact"])

    # XSLT basics
    register_xslt_function("generate_markdown", generate_markdown)
    register_xslt_function("image_to_base64", image_to_base64)
    register_xslt_function("current_document", current_document)

    register_qwebchannel_class("proteusBasics", ProteusBasicMethods)

