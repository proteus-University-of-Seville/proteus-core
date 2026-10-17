# ==========================================================================
# File: __init__.py
# Description: module initialization for the PROTEUS application package
# Date: 25/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

import re

# PyQt6 Search Paths
RESOURCES_SEARCH_PATH = "resources"
THEME_SEARCH_PATH = "theme"
TEMPLATE_DUMMY_SEARCH_PATH = "templates"
ASSETS_DUMMY_SEARCH_PATH = "assets"

# Only the dummy URLs in attributes (src="assets:///image.png") are replaced
# with the real ones. The same text in the content of an object (e.g. the
# syntax of an image in a Markdown text explained in a comment) must be left
# as it was written.
_ASSETS_ATTRIBUTE_URL_PATTERN = re.compile('(?<=")' + ASSETS_DUMMY_SEARCH_PATH + ":///")


def replace_assets_urls(html: str, replacement: str) -> str:
    """
    Replaces the dummy assets URLs of the attributes of an HTML string with
    the given string, e.g. 'file:///<project>/assets/'.
    """
    return _ASSETS_ATTRIBUTE_URL_PATTERN.sub(lambda match: replacement, html)
