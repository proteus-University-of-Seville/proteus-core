# ==========================================================================
# File: main_window.py
# Description: PyQT6 main view for the PROTEUS application
# Date: 11/05/2023
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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QMessageBox, QHBoxLayout, QLabel

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_NAME
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.application.metrics import Metrics
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.themes import Themes
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.main_menu import MainMenu
from proteus.views.components.project_container import ProjectContainer
from proteus.application.events import (
    SelectObjectEvent,
    OpenProjectEvent,
    ModifyObjectEvent,
    ClipboardChangedEvent,
    UpdateMetricsEvent,
    ThemeChangedEvent,
)
from proteus.application.state.exporter import write_state_to_file
from proteus.application.clipboard import Clipboard, ClipboardStatus

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: MainWindow
# Description: Main window class for the PROTEUS application.
# Date: 11/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MainWindow(QMainWindow, ProteusComponent):
    """
    Main window for the PROTEUS application. It is used to display the main
    menu and the documents tab menu. Update the main window when a new
    project is opened.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the main window.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.
        """
        super(MainWindow, self).__init__(*args, **kwargs)

        # Variables
        self.main_menu: MainMenu = None
        self.project_container: ProjectContainer = None

        # Create the component
        self.create_component()

        # Subscribe to events
        self.subscribe()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the main window for the PROTEUS application.
    # Date       : 16/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the main window for the PROTEUS application.
        """
        # Set the window title
        self.setWindowTitle(_("main_window.title"))

        # Set the window icon
        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

        # Set the window size
        self.resize(1200, 800)

        # Create main menu
        self.main_menu = MainMenu(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.main_menu)

        # Create document list menu
        self.project_container = QWidget(self)
        self.setCentralWidget(self.project_container)

        # Create the status bar
        self.statusBar().showNormal()

        # Create the clipboard indicator
        self.clipboard_indicator = ClipboardIndicator(parent=self)
        self.metrics_indicator = MetricsIndicator(parent=self)

        self.statusBar().addPermanentWidget(self.clipboard_indicator)
        self.statusBar().addPermanentWidget(self.metrics_indicator)

        log.info("Main window component created")

    # ---------------------------------------------------------------------
    # Method     : subscribe
    # Description: Subscribe the component to the events.
    # Date       : 15/11/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def subscribe(self) -> None:
        """
        Subscribe the component to the events.

        MainMenu component subscribes to the following events:
            - OPEN PROJECT -> update_on_open_project
            - SELECT OBJECT -> update_on_select_object
            - MODIFY OBJECT -> update_on_modify_object
            - THEME CHANGED -> update_on_theme_changed
        """

        OpenProjectEvent().connect(self.update_on_open_project)
        SelectObjectEvent().connect(self.update_on_select_object)
        ModifyObjectEvent().connect(self.update_on_modify_object)
        ThemeChangedEvent().connect(self.update_on_theme_changed)

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_on_open_project
    # Description: Update the main window when a new project is opened.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_open_project(self) -> None:
        """
        Update the main window when a new project is opened. It is used to
        load the document list menu and update the window title.

        Triggered by: OpenProjectEvent
        """
        # Delete the existing widget or container
        if self.project_container.__class__ == QWidget:
            self.project_container.setParent(None)
        elif self.project_container.__class__ == ProjectContainer:
            self.project_container.delete_component()

        # Create document list menu
        self.project_container = ProjectContainer(self)
        self.setCentralWidget(self.project_container)

        project = self._controller.get_current_project()
        self.setWindowTitle(
            f"{_('main_window.title')} - {project.get_property(PROTEUS_NAME).value}"
        )

    # ----------------------------------------------------------------------
    # Method     : update_on_select_object
    # Description: Update the status bar when a new object is selected.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_select_object(
        self, selected_object_id: ProteusID, document_id: ProteusID
    ) -> None:
        """
        Update the status bar when a new object is selected. It is used to
        show information about the current selected object to the user.

        Triggered by: SelectObjectEvent

        :param selected_object_id: Id of the selected object
        :param document_id: Id of the document where the object is located
        """
        # NOTE: Adding a permanent message to the status bar is discouraged
        #       due to the fact that it is not possible to remove it just
        #       hide it using removeWidget() method.
        # https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qstatusbar.html#qstatusbar-permanent-message

        # If there is no selected object, return
        if selected_object_id is None or selected_object_id == "":
            return

        assert (
            document_id is not None or document_id != ""
        ), "Document id is None on SELECT OBJECT event"

        # If the selected object is not in the current document, return
        if document_id != self._state_manager.get_current_document():
            return

        # Get the selected object and its name
        selected_object: Object = self._controller.get_element(selected_object_id)
        object_name = selected_object.get_property(PROTEUS_NAME).value

        translated_object_accepted_children = [
            _(f"archetype.class.{cls}", alternative_text=cls).lower()
            for cls in selected_object.acceptedChildren
        ]

        translated_object_accepted_parents = [
            _(f"archetype.class.{cls}", alternative_text=cls).lower()
            for cls in selected_object.acceptedParents
        ]

        # Message to show in the status bar
        message: str = _(
            "main_window.statusbar.text.selected_object",
            selected_object_id,
            object_name,
            translated_object_accepted_children,
            translated_object_accepted_parents,
        )

        # Update the status bar with the temporary message
        self.statusBar().showMessage(message)

    # ----------------------------------------------------------------------
    # Method     : update_on_modify_object
    # Description: Update the window title when the project name is modified.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_modify_object(self, object_id: ProteusID) -> None:
        """
        Update the window title when the project name is modified. Check if
        the modified object is the project and update the window title.

        Triggered by: ModifyObjectEvent

        :param object_id: Id of the modified object
        """
        # Check the element id is not None
        assert object_id is not None, "Object id is None on MODIFY_OBJECT event"

        # Get project
        project: Project = self._controller.get_current_project()

        # Check if element id is project id
        if object_id == project.id:
            self.setWindowTitle(
                f"{_('main_window.title')} - {project.get_property(PROTEUS_NAME).value}"
            )

    # ======================================================================
    # Component slots methods
    # ======================================================================

    def update_on_theme_changed(self, theme_key: str) -> None:
        """
        Re-apply the window icon when the application theme changes.

        Triggered by: ThemeChangedEvent

        :param theme_key: Key of the newly applied theme.
        """
        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

    # ----------------------------------------------------------------------
    # Method     : closeEvent
    # Description: Handle the close event for the main window.
    # Date       : 15/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    # NOTE: This method overrides the default closeEvent method for the
    #       QMainWindow class. Close window dialog may be moved to its
    #       own class in the dialog package but closeEvent method must
    #       be overriden anyway.
    def closeEvent(self, event) -> None:
        """
        Handle the close event for the main window. Check if the project
        has unsaved changes and show a confirmation dialog to the user.

        Write the state to a file inside project folder if the user saves
        the project or close the application and no changes are discarded.

        :param event: Close event
        """

        def close_without_saving():
            # Clean the command stack
            self._controller.stack.clear()

            if not unsaved_changes:
                # Write the state to a file if there is a project opened
                if self._controller.get_current_project() is not None:
                    write_state_to_file()
            # Close the application
            event.accept()

        def close_with_saving():
            # Save the project
            self._controller.save_project()

            # Write the state to a file
            write_state_to_file()

            # Close the application
            event.accept()

        def cancel(*args, **kwargs):
            # Do nothing
            event.ignore()

        # Check if the project has unsaved changes
        unsaved_changes: bool = self._controller.check_unsaved_changes()

        if unsaved_changes:
            # Show a confirmation dialog
            confirmation_dialog = QMessageBox()
            confirmation_dialog.setIcon(QMessageBox.Icon.Warning)
            proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
            confirmation_dialog.setWindowIcon(proteus_icon)
            confirmation_dialog.setWindowTitle(_("main_window.exit_dialog.title"))
            confirmation_dialog.setText(_("main_window.exit_dialog.text"))
            confirmation_dialog.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            confirmation_dialog.button(QMessageBox.StandardButton.Yes).setText(
                _("dialog.yes_button")
            )
            confirmation_dialog.button(QMessageBox.StandardButton.No).setText(
                _("dialog.no_button")
            )

            confirmation_dialog.setDefaultButton(QMessageBox.StandardButton.No)
            confirmation_dialog.accepted.connect(close_with_saving)
            confirmation_dialog.rejected.connect(close_without_saving)
            confirmation_dialog.closeEvent = cancel
            confirmation_dialog.exec()
        else:
            close_without_saving()


class ClipboardIndicator(QWidget, ProteusComponent):
    """
    Class that provides a visual indicator for the clipboard status.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.
        """
        super(ClipboardIndicator, self).__init__(*args, **kwargs)

        # Create the component
        self.create_component()

        # Subscribe to events
        self.subscribe()

    def create_component(self) -> None:
        """
        Create the clipboard indicator component.
        """

        # Set the widget margins to zero
        self.setContentsMargins(0, 0, 0, 0)

        self.container_widget = QWidget()
        self.container_widget.setObjectName("clipboard_indicator")

        # Create the clipboard icon and message labels
        self._clipboard_message_label = QLabel(_("clipboard.indicator.status.empty"))
        self._object_icon_label = QLabel()
        self._object_information_label = QLabel()

        self._object_icon_label.hide()
        self._object_information_label.hide()

        # Create icon label
        self._clipboard_icon_label = QLabel()
        icon = Icons().icon(ProteusIconType.App, "clipboard_icon")
        icon_size: int = Themes().metric("icon_size_statusbar", 16)
        self._clipboard_icon_label.setPixmap(icon.pixmap(icon_size, icon_size))

        # Create an horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self._clipboard_icon_label)
        layout.addWidget(self._clipboard_message_label)
        layout.addWidget(self._object_icon_label)
        layout.addWidget(self._object_information_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.container_widget.setLayout(layout)

        # Creating a container widget is the only way to correctly set the
        # style to all the labels from the qss file.
        aux_layout = QHBoxLayout()
        aux_layout.addWidget(self.container_widget)
        aux_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(aux_layout)

    def subscribe(self) -> None:
        """
        Subscribe the component to the events.

        ClipboardIndicator component subscribes to the following events:
            - CLIPBOARD CHANGED -> update_on_clipboard_changed
            - THEME CHANGED -> update_on_theme_changed
        """

        ClipboardChangedEvent().connect(self.update_on_clipboard_changed)
        ThemeChangedEvent().connect(self.update_on_theme_changed)

    def update_on_theme_changed(self, theme_key: str) -> None:
        """
        Re-apply the status bar icons when the application theme changes.
        The clipboard status update re-reads every icon and pixmap.

        Triggered by: ThemeChangedEvent

        :param theme_key: Key of the newly applied theme.
        """
        icon_size: int = Themes().metric("icon_size_statusbar", 16)
        icon = Icons().icon(ProteusIconType.App, "clipboard_icon")
        self._clipboard_icon_label.setPixmap(icon.pixmap(icon_size, icon_size))

        self.update_on_clipboard_changed()

    def update_on_clipboard_changed(self) -> None:
        """
        Update the clipboard indicator when the clipboard status changes.
        It is used to show information about the current clipboard status
        to the user.

        Triggered by: ClipboardChangedEvent
        """

        # Get the clipboard status
        clipboard_status = Clipboard().get_status()

        if clipboard_status == ClipboardStatus.CLEAR:
            self._clipboard_message_label.setText(_("clipboard.indicator.status.empty"))
            self._object_information_label.setText("")
            self._object_icon_label.clear()

            self._object_icon_label.hide()
            self._object_information_label.hide()
            return

        # Retrieve clipboard content data
        clipboard_content = Clipboard().get_content()
        object = self._controller.get_element(clipboard_content)
        object_name = object.get_property(PROTEUS_NAME).value
        object_class = object.classes[-1]
        object_icon = Icons().icon(ProteusIconType.Archetype, object_class)

        # Update the status bar with the temporary message
        if clipboard_status == ClipboardStatus.COPY:
            self._clipboard_message_label.setText(
                _("clipboard.indicator.status.copied")
            )
        elif clipboard_status == ClipboardStatus.CUT:
            self._clipboard_message_label.setText(_("clipboard.indicator.status.cut"))

        icon_size: int = Themes().metric("icon_size_statusbar", 16)
        self._object_icon_label.setPixmap(object_icon.pixmap(icon_size, icon_size))
        self._object_information_label.setText(object_name)

        self._object_icon_label.show()
        self._object_information_label.show()


class MetricsIndicator(QWidget, ProteusComponent):
    """
    Simple widget that displays metrics information in the status bar.
    """

    def __init__(self, parent=None):
        super(MetricsIndicator, self).__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)

        # Create the labels
        self._html_generation_time_label = QLabel()
        self._html_load_time_label = QLabel()

        self._html_generation_time_label.hide()
        self._html_load_time_label.hide()

        # Create an horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self._html_generation_time_label)
        layout.addWidget(self._html_load_time_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        UpdateMetricsEvent().connect(self.update_metrics)

    def update_metrics(self):
        """
        Update the metrics information in the status bar.
        """
        self._html_generation_time_label.setText(
            _(
                "main_window.statusbar.text.html_generation_time",
                Metrics.html_generation_time,
            )
        )
        self._html_load_time_label.setText(
            _("main_window.statusbar.text.html_load_time", Metrics.html_load_time)
        )

        self._html_generation_time_label.show()
        self._html_load_time_label.show()
