# ==========================================================================
# File: markdown_property_input.py
# Description: Markdown property input widget for properties forms.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.properties.markdown_property import MarkdownProperty
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.markdown_edit import MarkdownEdit


# --------------------------------------------------------------------------
# Class: MarkdownPropertyInput
# Description: Markdown property input widget for properties forms.
# Date: 17/10/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MarkdownPropertyInput(PropertyInput):
    """
    Markdown property input widget for properties forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wrap_in_group_box = True

    # ----------------------------------------------------------------------
    # Method     : get_value
    # Description: Returns the value of the input widget.
    # Date       : 04/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def get_value(self) -> str:
        """
        Returns the value of the input widget.
        """
        self.input: MarkdownEdit
        return self.input.markdown()

    # ----------------------------------------------------------------------
    # Method     : validate
    # Description: Validates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def validate(self) -> str | None:
        """
        Validates the input widget. Returns an error message if the input
        has errors, None otherwise.

        Text cannot contain CDATA section delimiters because it is used
        to store the value of the property.
        """
        text: str = self.get_value()

        # Check if text contains CDATA section delimiters
        if text.find("<![CDATA[") != -1 or text.find("]]>") != -1:
            return "markdown_property_input.validator.error.cdata"
        
        # Check required
        if self.property.required and (text is None or text == ""):
            return "property_input.validator.error.required"

        return None

    # ----------------------------------------------------------------------
    # Method     : create_input
    # Description: Creates the input widget.
    # Date       : 17/10/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_input(property: MarkdownProperty, *args, **kwargs) -> MarkdownEdit:
        """
        Creates the input widget based on MarkdownEdit.
        """
        input: MarkdownEdit = MarkdownEdit()
        input.setMarkdown(property.value)
        return input
