# ==========================================================================
# File: views_container.py
# Description: PyQT6 views container component for the PROTEUS application
# Date: 04/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Dict
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QByteArray, QUrl, QSize
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QTabBar,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID
from proteus.application.metrics import Metrics
from proteus.application.resources.translator import translate as _
from proteus.application.configuration.config import Config
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.plugins import Plugins
from proteus.application.events import (
    ModifyObjectEvent,
    AddViewEvent,
    DeleteViewEvent,
    AddObjectEvent,
    DeleteObjectEvent,
    CurrentDocumentChangedEvent,
    CurrentViewChangedEvent,
    SelectObjectEvent,
    SortChildrenEvent,
    ChangeObjectPositionEvent,
)
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.dialogs.new_view_dialog import NewViewDialog
from proteus.views.components.dialogs.export_dialog import ExportDialog

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ViewsContainer
# Description: PyQT6 views container class for the PROTEUS application
# Date: 04/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ViewsContainer(QTabWidget, ProteusComponent):
    """
    Views container component for the PROTEUS application. It contains
    a browser for each project view. Displays the current document
    representation for each view.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 04/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, parent: QWidget, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.

        Store the browsers in a dict to access them by the view name. Using
        multiple browsers is a solution to use QTabWidget since a QWebEngineView
        cannot be added to multiple parents.

        :param parent: Parent widget.
        """
        super(ViewsContainer, self).__init__(parent, *args, **kwargs)
        # Dict of stored browsers for each view. The way the dict is updated
        # the index of the browser is the same as the index of the tab.
        # NOTE: Dictionaries are ordered since Python 3.7. We can parse the
        #       dict to a list to get the browsers in the same order as the
        #       tabs.
        # NOTE: QWebEngineView is used instead QTextBrowser because it supports
        #       javascript, external resources and other features that are
        #       needed to render the document.
        # NOTE: Multiple browsers are a solution to QTabWidget since a
        #       QWebEngineView cannot be added to multiple parents.
        self.tabs: Dict[str, QWebEngineView] = {}

        self.add_view_button: QPushButton
        self.export_view_button: QPushButton

        # Create the component
        self.create_component()

        # Connect tab close signal to the close_tab method
        self.tabCloseRequested.connect(self.close_tab)

        # Connect update methods to the events
        self.subscribe()

        # Call the current view changed method to update the document for the
        # first time if there are views
        if len(self.tabs) > 0:
            self.current_view_changed(index=0)

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the views container component.
    # Date       : 04/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the views container component.
        """
        # Allow to close tabs
        self.setTabsClosable(True)

        current_default_view: str = Config().app_settings.default_view

        self.add_view(current_default_view)

        # Check at least one view is available
        assert (
            len(self.tabs) > 0
        ), "Project selected templates and default template were not found in XSLT directory, there is no views to display!"

        # Create a button to add new views
        add_view_button_icon = Icons().icon(ProteusIconType.App, "add_view_icon")
        self.add_view_button: QPushButton = QPushButton()
        self.add_view_button.setIcon(add_view_button_icon)
        self.add_view_button.setToolTip(_("add_view_button.tooltip"))

        # Create a button to export views (duplicated from main menu)
        export_view_button_icon = Icons().icon(ProteusIconType.MainMenu, "export")
        self.export_view_button: QPushButton = QPushButton()
        self.export_view_button.setIcon(export_view_button_icon)
        self.export_view_button.setToolTip(_("export_button.tooltip"))

        wrapper = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 10, 8)
        layout.addWidget(self.export_view_button)
        layout.addWidget(self.add_view_button)
        wrapper.setLayout(layout)
        

        self.add_view_button.clicked.connect(
            lambda: NewViewDialog.create_dialog(self._controller)
        )

        self.export_view_button.clicked.connect(
            lambda: ExportDialog.create_dialog(self._controller)
        )

        self.setCornerWidget(wrapper, Qt.Corner.TopRightCorner)

        # Hide the close button on the main view tab
        try:
            self.tabBar().tabButton(0, QTabBar.ButtonPosition.RightSide).hide()
        except AttributeError:
            log.debug(
                "Tab bar button not found in the RightSide position. Ignore this message on MacOS."
            )

        # Connect singal to handle view tab change
        self.currentChanged.connect(self.current_view_changed)

        log.info("Views container component created")

    # ----------------------------------------------------------------------
    # Method     : add_view
    # Description: Add a new view to the views container component.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_view(self, xslt_name: str) -> None:
        """
        Add a new view to the views container component.

        :param xslt_name: Name of the xslt file.
        """
        if xslt_name not in self._controller.get_available_xslt():
            log.error(
                f"XSLT template {xslt_name} not found in the XSLT directory, view not added to the views container component."
            )
            self._state_manager.remove_opened_view(xslt_name)
            return

        if xslt_name in self.tabs.keys():
            log.debug(
                f"XSLT template {xslt_name} already exists in the views container component."
            )
            return

        # Create browser
        browser: QWebEngineView = QWebEngineView(self)
        browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # Create document page using subclass
        # NOTE: This subclass is needed for external links handling
        document_page: DocumentPage = DocumentPage(parent=browser)
        browser.setPage(document_page)

        # QWebChannel setup for plugins
        channel_objects: Dict[str, ProteusComponent] = {}
        for name, _class in Plugins().get_qwebchannel_classes().items():
            channel_object = _class(parent=self)
            channel_objects[name] = channel_object

        channel: QWebChannel = QWebChannel(browser)
        channel.registerObjects(channel_objects)
        browser.page().setWebChannel(channel)
        # NOTE: registeredObjects method causes a crash when the channel is loaded
        #       in the browser. This is a PyQt6 bug, works in PySide6.
        # log.debug(f"Registered QWebChannel objects: {channel.registeredObjects()}")

        # Build the tab code name
        # NOTE: The tab code name is used to access the tab name internationalization
        tab_code_name: str = f"xslt_templates.{xslt_name}"

        # Set layout, add tab
        # NOTE: Tabs are added in the same order as the browsers are stored,
        #       always at the end.
        tab_index = self.addTab(browser, _(tab_code_name, alternative_text=xslt_name))

        icon = Icons().icon(ProteusIconType.App, "view_icon")
        self.setTabIcon(tab_index, icon)
        self.setIconSize(QSize(32, 32))

        # Store the browser in the tab dict
        self.tabs[xslt_name] = browser

        # Add the opened view to the state manager
        self._state_manager.add_opened_view(xslt_name)

    # ----------------------------------------------------------------------
    # Method     : subscribe
    # Description: Subscribe the component to the events.
    # Date       : 15/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def subscribe(self) -> None:
        """
        Subscribe the component to the events.

        ViewsContainer component subscribes to the following events:
            - ADD OBJECT -> update_view
            - MODIFY OBJECT -> update_view
            - DELETE OBJECT -> update_view
            - CURRENT DOCUMENT CHANGED -> update_view
            - SORT CHILDREN -> update_view
            - CHANGE OBJECT POSITION -> update_view
            - ADD VIEW -> update_on_add_view
            - DELETE VIEW -> update_on_delete_view
            - SELECT OBJECT -> update_on_select_object
            - CURRENT VIEW CHANGED -> update_on_current_view_changed
        """
        AddObjectEvent().connect(self.update_view_on_add_object)
        ModifyObjectEvent().connect(self.update_view)
        DeleteObjectEvent().connect(self.update_view)
        CurrentDocumentChangedEvent().connect(self.update_view)
        SortChildrenEvent().connect(self.update_view)
        ChangeObjectPositionEvent().connect(self.update_view)

        AddViewEvent().connect(self.update_on_add_view)
        DeleteViewEvent().connect(self.update_on_delete_view)
        SelectObjectEvent().connect(self.update_on_select_object)
        CurrentViewChangedEvent().connect(self.update_on_current_view_changed)

    # ----------------------------------------------------------------------
    # Method     : display_view
    # Description: Update the view to display the current project
    # Date       : 04/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def display_view(self, object_to_scroll: ProteusID = None) -> None:
        """
        Update the view to display the current project information rendered
        using the current view template. If there is no current document
        (all documents deleted), clear the browser.
        """
        # Get the current document id and the current view
        current_document_id: ProteusID = self._state_manager.get_current_document()
        current_view: str = self._state_manager.get_current_view()

        # If the current view is not in the browsers dict, ignore the update
        if current_view not in self.tabs:
            log.error(f"View {current_view} not found in the views container component")
            return

        # Get the browser for the current view
        browser: QWebEngineView = self.tabs[current_view]

        # If there is no current document, clear the browser
        if current_document_id is None:
            browser.page().setContent(QByteArray(), "text/html")
            return

        # Update the current view browser with the content
        if current_view in self.tabs and current_document_id is not None:
            # Get html from controller
            html_path: str = self._controller.get_html_view_path(xslt_name=current_view)

            Metrics.html_load_time_start()

            browser.loadFinished.connect(
                lambda: self.load_finished(browser.loadFinished, object_to_scroll)
            )

            url: QUrl = QUrl.fromLocalFile(html_path)
            log.debug(f"Loading HTML file: {url.toString()}")
            browser.page().load(url)

            # NOTE: When using onLoadFinished signal make sure to disconnect
            # the sender using self.sender().disconnect() to avoid multiple
            # calls when page is reloaded.

    def load_finished(self, sender: QWebEngineView.loadFinished, object_to_scroll: ProteusID):  # type: ignore
        # Disconnect the signal to avoid multiple calls when page is reloaded
        sender.disconnect()

        current_selected_object: ProteusID = self._state_manager.get_current_object()
        current_view: str = self._state_manager.get_current_view()

        # If an object is given to scroll, scroll to it
        if object_to_scroll is not None:
            script_template: str = "onTreeObjectSelected('{}');"
            browser: QWebEngineView = self.tabs[current_view]
            browser.page().runJavaScript(script_template.format(object_to_scroll))
        # If not, scroll to the current selected object
        elif current_selected_object is not None:
            script_template: str = "onTreeObjectSelected('{}');"
            browser: QWebEngineView = self.tabs[current_view]
            browser.page().runJavaScript(
                script_template.format(current_selected_object)
            )

        Metrics.html_load_time_end()

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_view_on_add_object
    # Description: Update the view when an object is added to the project.
    # Date       : 01/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_view_on_add_object(
        self, object_id: ProteusID, update_view: bool
    ) -> None:
        """
        Update the view when an object is added to the project.

        Triggered by: AddObjectEvent

        :param object_id: Id of the added object.
        :param update_view: Flag to update the view.
        """
        if update_view is True:
            self.display_view(object_id)

    # ----------------------------------------------------------------------
    # Method     : update_view
    # Description: Update the view depending on the update_view flag.
    # Date       : 01/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_view(self, _, update_view: bool) -> None:
        """
        Update the view depending on the update_view flag.

        Triggered by:   ModifyObjectEvent, DeleteObjectEvent,
                        CurrentDocumentChangedEvent, CurrentViewChangedEvent

        :param _: Unused parameter.
        :param update_view: Flag to update the view.
        """
        if update_view is True:
            self.display_view()

    # ----------------------------------------------------------------------
    # Method     : update_on_current_view_changed
    # Description: Update the document render component when the current
    #              view is changed.
    # Date       : 02/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_current_view_changed(self, view_name: str, update_view: bool) -> None:
        """
        Update the document render component when the current view is
        changed.

        Triggered by: CurrentViewChangedEvent

        :param view_name: Name of the view to display.
        :param update_view: Flag to update the view.
        """
        # If the view is not in the tabs dict, ignore the update
        if view_name not in self.tabs:
            log.error(f"View {view_name} not found in the views container component")
            return

        # Set the current tab to the view tab if not already selected
        view_tab: QWebEngineView = self.tabs[view_name]
        if self.currentIndex() != self.indexOf(view_tab):
            tab_index: int = self.indexOf(view_tab)
            self.setCurrentIndex(tab_index)

        # Check update_view flag
        if update_view is True:
            self.display_view()

    # ----------------------------------------------------------------------
    # Method     : update_on_add_view
    # Description: Update the document render component when a new view is
    #              added to the project.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_add_view(self, view_name: str) -> None:
        """
        Update the document render component when a new view is added to
        the project documents. Add a new tab to each document. If the
        view already exists, do nothing.

        Triggered by: AddViewEvent

        :param view_name: Name of the view to add.
        """
        # If the view already exists, do nothing
        if view_name in self.tabs.keys():
            return

        self.add_view(view_name)

    # ----------------------------------------------------------------------
    # Method     : update_on_select_object
    # Description: Update the document render component when an object is
    #              selected.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_select_object(
        self, selected_object_id: ProteusID, document_id: ProteusID, navigate: bool
    ) -> None:
        """
        Update the views container component when an object is selected.
        Navigate to the object in the document given the object id.

        Triggered by: SelectObjectEvent

        :param selected_object_id: Id of the selected object.
        :param document_id: Id of the document where the object is located.
        """
        # If there is no selected object or the document is not the current
        # document, do nothing
        if selected_object_id is None:
            return

        if document_id != self._state_manager.get_current_document():
            return

        if navigate is False:
            return

        # NOTE: This javascript function must be implemented in the xslt
        #       template. If not implemented, a js error will be shown in
        #       the python console.
        script_template: str = "onTreeObjectSelected('{}');"

        # Get current view
        current_view: str = self._state_manager.get_current_view()

        # Run the script in the current view browser
        if current_view in self.tabs:
            browser: QWebEngineView = self.tabs[current_view]

            browser.page().runJavaScript(script_template.format(selected_object_id))

    # ----------------------------------------------------------------------
    # Method     : update_on_delete_view
    # Description: Update the views container component when a view is
    #              deleted from the document.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_delete_view(self, view_name: str) -> None:
        """
        Update the views container component when a view is deleted from
        the project documents. Delete the tab from each document.

        Triggered by: DeleteViewEvent

        :param view_name: Name of the view to delete.
        """
        # Assert the view exists
        assert (
            view_name in self.tabs.keys()
        ), f"View {view_name} not found in tabs dict on DELETE VIEW event"

        # Get the index of the tab to delete
        tab: int = self.tabs[view_name]
        tab_index: int = self.indexOf(tab)

        # Delete the tab
        self.removeTab(tab_index)
        self.update()

        browser: QWebEngineView = self.tabs.pop(view_name)

        # Delete from state manager
        self._state_manager.remove_opened_view(view_name)

        # Delete the browser
        browser.parent = None
        browser.deleteLater()

    # ======================================================================
    # Component methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : close_tab
    # Description: Close the tab with the given index.
    # Date       : 23/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def close_tab(self, index: int) -> None:
        """
        Triggered when the user closes a tab. Get the xslt name and call
        the controller to delete the view and delete template from project
        file.

        :param index: Index of the tab to close.
        """
        # Get the key corresponding to the tab index
        xslt_name: str = list(self.tabs.keys())[index]

        # Trigger REMOVE_VIEW event
        DeleteViewEvent().notify(xslt_name)

    # ----------------------------------------------------------------------
    # Method     : current_view_changed
    # Description: Slot triggered when the current view tab is changed.
    #              It updates the current view in the state manager.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def current_view_changed(self, index: int) -> None:
        """
        Slot triggered when the current document tab is changed. It updates
        the current view in the state manager.

        :param index: Index of the current tab.
        """
        # Get view name from the tab index
        view_name: str = None
        if index >= 0:
            view_tab: QWidget = self.widget(index)
            # Get the document id (key) from the tab (value)
            view_name = list(self.tabs.keys())[list(self.tabs.values()).index(view_tab)]

        # Update current document in the state manager
        self._state_manager.set_current_view(view_name)


# --------------------------------------------------------------------------
# Class: DocumentPage
# Description: Document Page class. Subclass of QWebEnginePage.
# Date: 30/06/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class DocumentPage(QWebEnginePage):
    """
    Subclass of QWebEnginePage. Used to override the acceptNavigationRequest
    method to avoid opening external links in the browser.
    """

    # ----------------------------------------------------------------------
    # Method     : acceptNavigationRequest
    # Description: Override the acceptNavigationRequest method to avoid
    #              opening external links in the browser.
    # Date       : 30/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def acceptNavigationRequest(
        self, url: QUrl, _type: QWebEnginePage.NavigationType, isMainFrame: bool
    ) -> bool:
        """
        Override the acceptNavigationRequest method to avoid opening
        external links in the browser. If the link is a link to an
        external page, ask the user if he wants to open it in system
        default browser.
        """
        # If the link is a link to an external page, ask the user if he
        # wants to open it in system default browser.
        if (
            _type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked
            and not url.isLocalFile()
        ):
            # Ask the user if he wants to open the link in the system
            # default browser
            message_box_pressed_button = MessageBox.question(
                _("document_render.external_link"),
                _("document_render.external_link.text", url.toString()),
            )

            # If the user wants to open the link in the system default
            # browser, open it
            if message_box_pressed_button == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(url)
                return False
            else:
                return False

        return super().acceptNavigationRequest(url, _type, isMainFrame)

    # ----------------------------------------------------------------------
    # Method     : javaScriptConsoleMessage
    # Description: Override the javaScriptConsoleMessage method to avoid
    #              printing javascript errors in the python console.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def javaScriptConsoleMessage(
        self,
        level: QWebEnginePage.JavaScriptConsoleMessageLevel,
        message: str,
        line: int,
        sourceId: str,
    ) -> None:
        """
        Override the javaScriptConsoleMessage method to avoid printing
        javascript errors in the python console.

        Uses the logging module to print javascript messages in the main
        PROTEUS log file.
        """
        # Get the log level
        log_level: int = logging.INFO
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            log_level = logging.WARNING
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            log_level = logging.ERROR

        # Print the message in the log file
        log.log(log_level, f"QWebEnginePage console | {message}")
