# ==========================================================================
# File: project_container.py
# Description: PyQT6 project container component for the PROTEUS application
# Date: 03/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QSplitter, QWidget

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.themes import Themes
from proteus.application.events import ThemeChangedEvent
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.documents_container import DocumentsContainer
from proteus.views.components.views_container import ViewsContainer

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: ProjectContainer
# Description: PyQT6 project container class for the PROTEUS application
# Date: 03/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ProjectContainer(QWidget, ProteusComponent):
    """
    Container for the project information. It contains a tab widget with the
    documents of the project and a tab widget with the project views.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 03/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self, parent: QWidget, *args, **kwargs
    ) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.

        Store the tabs for each document in a dictionary to access them
        later. Also store the children components of each tab in a
        dictionary to delete when the tab is closed.

        :param parent: Parent widget.
        """
        super(ProjectContainer, self).__init__(parent, *args, **kwargs)

        # Children components
        self.documents_container: DocumentsContainer = None
        self.views_container: ViewsContainer = None

        # Create the component
        self.create_component()
        self.subscribe()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the documents tab menu component
    # Date       : 03/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the project container component. Initialize its children
        (DocumentsContainer and ViewsContainer) and add them to an splitter
        widget.
        """

        # Create project container layout
        tab_layout: QHBoxLayout = QHBoxLayout(self)

        # Splitter
        splitter: QSplitter = QSplitter()

        # DocumentsContainer -------------------------------------------------
        self.documents_container: DocumentsContainer = DocumentsContainer(
            parent=self
        )
        self.documents_container.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )

        # ViewsContainer -----------------------------------------------------
        self.views_container: ViewsContainer = ViewsContainer(
            parent=self
        )
        self.views_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._apply_theme_widths()

        # Add tree and render to splitter
        splitter.addWidget(self.documents_container)
        splitter.addWidget(self.views_container)
        # NOTE: By default the splitter is 1200px wide when the application
        #       is launched. We set the initial sizes proportionally to the
        #       splitter size to avoid the render component to be too small
        splitter.setSizes([300, 900])

        # Add splitter with tree and render to tab layout
        tab_layout.addWidget(splitter)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        self.setLayout(tab_layout)

        log.info("Project container component created")

    def subscribe(self) -> None:
        """Refresh the existing splitter children when theme metrics change."""
        ThemeChangedEvent().connect(self.update_on_theme_changed)

    def update_on_theme_changed(self, theme_key: str) -> None:
        """Apply the active theme's minimum widths without rebuilding views."""
        self._apply_theme_widths()

    def _apply_theme_widths(self) -> None:
        self.documents_container.setMinimumWidth(Themes().metric("tree_min_width", 200))
        self.views_container.setMinimumWidth(Themes().metric("views_min_width", 400))

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ======================================================================
    # Component slots methods (connected to the component signals)
    # ======================================================================
