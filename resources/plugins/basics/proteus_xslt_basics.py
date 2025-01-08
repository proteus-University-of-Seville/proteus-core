# ==========================================================================
# File: proteus_xslt_basics.py
# Description: PROTEUS plugin that provides basic XSLT functions for use in
#              templates. Some of these functions are:
#              - generate_markdown: Generate markdown from a list of etree.Element
#              - image_to_base64: Creates the base64 representation of an image.
#              - current_document: Returns the current selected document.
#              ProteusBasicMethods class provides a method to access the current
#              selected object in the current document from the QWebChannel.
# Date: 03/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List
from pathlib import Path
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import markdown
import lxml.etree as ET
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, pyqtSlot

# --------------------------------------------------------------------------
# Plugins imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Proteus imports
# --------------------------------------------------------------------------

from proteus.application.state.manager import StateManager
from proteus.model import ASSETS_REPOSITORY
from proteus.views.components.abstract_component import ProteusComponent

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Function    : generate_markdown
# Description : Generate markdown from a list of etree.Element
# Date        : 29/06/2023
# Version     : 0.1
# Author      : José María Delgado Sánchez
# --------------------------------------------------------------------------
def generate_markdown(context, markdown_element: List[ET._Element]) -> str:
    """
    Generate markdown from a list of etree.Element. Markdown is generated
    from the text of the elements in the list.

    NOTE: Output HTML is not wrapped in <p>.
    """
    markdown_text = ""
    for element in markdown_element:
        markdown_text += element.text

    result: str = markdown.markdown(
        markdown_text,
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.tables",
            "markdown.extensions.toc",
        ],
    )

    # Remove the first <p> tag and the last </p> tag
    result = result.replace("<p>", "", 1)
    result = result[::-1].replace(">p/<", "", 1)[::-1]

    return result

# --------------------------------------------------------------------------
# Function    : image_to_base64
# Description : Creates the base64 representation of an image.
# Date        : 11/07/2023
# Version     : 0.1
# Author      : José María Delgado Sánchez
# --------------------------------------------------------------------------
def image_to_base64(context, asset_file: List[ET._Element]) -> str:
    """
    Given an asset file path, return the base64 representation of the image.
    Build the absolute path using the current project path and the assets
    repository name.
    """

    assets_path: Path = StateManager().current_project_path / ASSETS_REPOSITORY / asset_file[0].text

    # Load the image using QImage
    image = QImage(assets_path.as_posix())

    ba = QByteArray()
    buffer = QBuffer(ba)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    base64_data = ba.toBase64().data().decode()
    return base64_data


# --------------------------------------------------------------------------
# Function    : current_document
# Description : Returns the current document
# Date        : 21/12/2023
# Version     : 0.1
# Author      : José María Delgado Sánchez
# --------------------------------------------------------------------------
def current_document(context) -> str:
    """
    Returns the current selected document in the project context.
    """
    document_id = StateManager().get_current_document()
    return str(document_id)


# --------------------------------------------------------------------------
# Class      : ProteusBasicMethods
# Description: Class that defines the basic methods for PROTEUS HTML views.
# Date       : 18/01/2024
# Version    : 0.1
# Author     : José María Delgado Sánchez
# --------------------------------------------------------------------------
class ProteusBasicMethods(ProteusComponent):
    """
    Class that defines the basic methods for PROTEUS HTML views.

    It provides a method to access the current selected object in the current
    document.
    """
    @pyqtSlot(result=str)
    def get_current_object_id(self) -> str | None:
        """
        Returns the current selected object in the current document, or None if
        there is no object selected.
        """
        return self._state_manager.get_current_object()
    