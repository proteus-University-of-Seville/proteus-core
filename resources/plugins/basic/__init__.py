# ==========================================================================
# Plugin: basic
# Description: PROTEUS 'basic' plugin provides general XSLT utilities and
#              QWebChannel classes for PROTEUS.
# Date: 05/05/2025
# Version: 0.3
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

from basic.proteus_xslt_basics import generate_markdown, image_to_base64, current_document
from basic.proteus_xslt_basics import ProteusBasicMethods
from basic.document_interactions import DocumentInteractions
from basic.impact_analyzer import ImpactAnalyzer
from basic.export.export_html import ExportHTML
from basic.export.export_pdf import ExportPDF
from basic.glossary_handler import GlossaryHandler
from basic.traceability_matrix_helper import TraceabilityMatrixHelper


def register(register_xslt_function, register_qwebchannel_class, register_proteus_component, register_export_strategy):

    # Document Interactions
    register_qwebchannel_class("documentInteractions", DocumentInteractions)

    # Impact analyzer
    register_proteus_component("impactAnalyzer", ImpactAnalyzer, ["_calculate_impact"])

    # XSLT basics
    register_xslt_function("generate_markdown", generate_markdown)
    register_xslt_function("image_to_base64", image_to_base64)
    register_xslt_function("current_document", current_document)

    register_qwebchannel_class("proteusBasics", ProteusBasicMethods)

    # Export strategies
    register_export_strategy("pdf", ExportPDF)
    register_export_strategy("html", ExportHTML)

    # Glossary
    register_xslt_function("glossary_highlight", GlossaryHandler.highlight_glossary_items)
    register_proteus_component("glossaryHandler", GlossaryHandler)

    # Traceability Matrix
    register_proteus_component("traceabilityMatrixHelper", TraceabilityMatrixHelper, ["get_objects_from_classes", "check_dependency"])

