# ==========================================================================
# File: main_menu.py
# Description: PyQT6 main menubar for the PROTEUS application
# Date: 01/06/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List, Dict
import logging
import traceback
from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
    QDockWidget,
    QToolButton,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.configuration.config import Config
from proteus.model import ProteusID, PROJECT_FILE_NAME
from proteus.model.object import Object
from proteus.views.components.abstract_component import ProteusComponent
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.views.components.dialogs.new_project_dialog import NewProjectDialog
from proteus.views.components.dialogs.property_dialog import PropertyDialog
from proteus.views.components.dialogs.new_document_dialog import NewDocumentDialog
from proteus.views.components.dialogs.settings_dialog import SettingsDialog
from proteus.views.components.dialogs.export_dialog import ExportDialog
from proteus.views.components.dialogs.information_dialog import InformationDialog
from proteus.views.components.dialogs.delete_dialog import DeleteDialog
from proteus.views.components.dialogs.impact_analysis import ImpactAnalysisWindow
from proteus.views.components.archetypes_menu_dropdown import (
    ArchetypesMenuDropdown,
)
from proteus.views import buttons
from proteus.views.buttons import ArchetypeMenuButton
from proteus.application.state.restorer import read_state_from_file
from proteus.application.state.exporter import write_state_to_file
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.clipboard import Clipboard
from proteus.application.events import (
    SelectObjectEvent,
    OpenProjectEvent,
    SaveProjectEvent,
    CurrentDocumentChangedEvent,
    RequiredSaveActionEvent,
    StackChangedEvent,
    ClipboardChangedEvent,
    ArchetypeRepositoryChangedEvent,
)

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: MainMenu
# Description: PyQT6 main menu class for the PROTEUS application
# Date: 01/06/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class MainMenu(QDockWidget, ProteusComponent):
    """
    Main menu component for the PROTEUS application. It is used to
    display the main option tab and object archetypes separated by
    classes separated by tabs.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 29/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, parent: QWidget, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors, create
        the component and connect update methods to the events.

        Manage the creation of the instace variables to store updatable
        buttons (save, undo, redo, etc.) and the tab widget to display the
        different menus.

        :param parent: Parent widget.
        """
        super(MainMenu, self).__init__(parent, *args, **kwargs)

        # Main menu buttons
        self.new_button: QToolButton = None
        self.open_button: QToolButton = None
        self.save_button: QToolButton = None
        self.cut_button: QToolButton = None
        self.copy_button: QToolButton = None
        self.paste_button: QToolButton = None
        self.undo_button: QToolButton = None
        self.redo_button: QToolButton = None
        self.project_properties_button: QToolButton = None
        self.add_document_button: QToolButton = None
        self.delete_document_button: QToolButton = None
        self.settings_button: QToolButton = None
        self.export_document_button: QToolButton = None
        self.information_button: QToolButton = None
        # Developer buttons
        # NOTE: This buttons will not be created if developer features are disabled
        # If QToolButton is not added to a widget, they are deleted by the garbage
        # collector. Not instantiating them allows to check if they are created or not
        self.store_object_archetype_button: QToolButton = None
        self.store_document_archetype_button: QToolButton = None

        # Store archetype buttons by object class
        self.archetype_buttons: Dict[str, ArchetypeMenuButton] = {}

        # Tab widget to display app menus in different tabs
        self.tab_widget: QTabWidget = QTabWidget()

        # Archetype related tabs
        self.archetype_tabs: List[QWidget] = []

        # Create the component
        self.create_component()

        # Subscribe to events
        self.subscribe()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the object main tab menu component
    # Date       : 29/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the object archetype tab menu component. It creates a tab for
        each class of object archetypes and a main tab for the main menu.
        """

        # ------------------
        # Component settings
        # ------------------
        # Remove title bar and dock widget features
        self.setTitleBarWidget(QWidget())
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        # Set the menu to minimum size and disable vertical resizing
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        # --------------------
        # Create tabbed widget
        # --------------------
        # Add the main tab
        self.add_main_tab(_("main_menu.tab.home.name"))

        # Get the object archetypes
        object_archetypes_dict: Dict[str, Dict[str, List[Object]]] = (
            self._controller.get_first_level_object_archetypes()
        )
        # Create a tab for each type of object archetypes
        for type_name in object_archetypes_dict.keys():
            self.add_archetype_tab(type_name, object_archetypes_dict[type_name])

        # --------------------
        # Profile information
        # --------------------
        profile_metadata = Config().current_profile_metadata

        profile_information: QWidget = QWidget()
        profile_information.setObjectName("profile_information")
        icon_information_layout: QVBoxLayout = QVBoxLayout()

        profile_label: QLabel = QLabel(_("main_menu.profile_label"))
        profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label: QLabel = QLabel()
        profile_icon = QIcon(profile_metadata.image.as_posix())
        # The pixmap will keep the aspect ratio of the original image and will be
        # restricted to the minimum of the width and height values, in this case
        # the maximun height will be 32 pixels like the menu bar buttons. 2000 is
        # an arbitrary value to ensure the image is not stretched.
        icon_label.setPixmap(profile_icon.pixmap(2000, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        profile_name: QLabel = QLabel(profile_metadata.name)
        profile_name.setWordWrap(True)
        profile_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set profile name as tooltip
        profile_information.setToolTip(profile_name.text())

        # If the profile label text is too long, trim it
        if len(profile_name.text()) > 30:
            profile_name.setText(profile_name.text()[:30] + "...")

        icon_information_layout.addWidget(profile_label)
        icon_information_layout.addStretch()
        icon_information_layout.addWidget(icon_label)
        icon_information_layout.addWidget(profile_name)
        icon_information_layout.addStretch()
        profile_information.setLayout(icon_information_layout)

        # --------------------
        # Menu container
        # --------------------
        container: QWidget = QWidget()
        container.setObjectName("main_menu_container")
        container_layout: QHBoxLayout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 1)
        container_layout.setSpacing(0)
        container.setLayout(container_layout)

        # Add widgets to the container layout
        container_layout.addWidget(self.tab_widget)

        container_layout.addWidget(profile_information)

        # Set the container as the widget of the dock widget
        self.setWidget(container)

        log.info("Main menu component created")

    # ----------------------------------------------------------------------
    # Method     : add_main_tab
    # Description: Add the main tab to the tab widget.
    # Date       : 01/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_main_tab(self, tab_name: str) -> None:
        """
        Create the main menu tab and add it to the tab widget. It displays
        the main menu buttons of the PROTEUS application.

        :param tab_name: Name of the tab.
        """
        # Create the tab widget with a horizontal layout
        main_tab: QWidget = QWidget()
        tab_layout: QHBoxLayout = QHBoxLayout()
        main_tab.setObjectName("main_tab")

        # ---------
        # Project menu
        # ---------
        # New action
        self.new_button: QToolButton = buttons.main_menu_button(
            self,
            text="new_project_button.text",
            icon_key="new-project",
            tooltip="new_project_button.tooltip",
            statustip="new_project_button.statustip",
            enabled=True,
            shortcut="Ctrl+N",
        )
        self.new_button.clicked.connect(
            lambda: NewProjectDialog.create_dialog(self._controller)
        )

        # Open action
        self.open_button: QToolButton = buttons.main_menu_button(
            self,
            text="open_project_button.text",
            icon_key="open-project",
            tooltip="open_project_button.tooltip",
            statustip="open_project_button.statustip",
            enabled=True,
            shortcut="Ctrl+O",
        )
        self.open_button.clicked.connect(self.open_project)

        # Save action
        self.save_button: QToolButton = buttons.main_menu_button(
            self,
            text="save_project_button.text",
            icon_key="save",
            tooltip="save_project_button.tooltip",
            statustip="save_project_button.statustip",
            enabled=False,
            shortcut="Ctrl+S",
        )
        self.save_button.clicked.connect(self.save_project)

        # Project properties action
        self.project_properties_button: QToolButton = buttons.main_menu_button(
            self,
            text="project_properties_button.text",
            icon_key="edit",
            tooltip="project_properties_button.tooltip",
            statustip="project_properties_button.statustip",
            enabled=False,
            shortcut="Ctrl+P",
        )
        self.project_properties_button.clicked.connect(
            lambda: PropertyDialog.create_dialog(
                element_id=self._controller.get_current_project().id,
                controller=self._controller,
            )
        )

        # Add the buttons to the project menu widget
        project_menu: QWidget = buttons.button_group(
            [
                self.new_button,
                self.open_button,
                self.save_button,
                self.project_properties_button,
            ],
            "main_menu.button_group.project",
        )
        tab_layout.addWidget(project_menu)
        tab_layout.addWidget(buttons.get_separator(vertical=True))

        # ---------
        # Document menu
        # ---------
        # Add document action
        self.add_document_button: QToolButton = buttons.main_menu_button(
            self,
            text="add_document_button.text",
            icon_key="new-file",
            tooltip="add_document_button.tooltip",
            statustip="add_document_button.statustip",
            enabled=False,
            shortcut="Ctrl+D",
        )
        self.add_document_button.clicked.connect(
            lambda: NewDocumentDialog.create_dialog(self._controller)
        )

        # Delete document action
        self.delete_document_button: QToolButton = buttons.main_menu_button(
            self,
            text="delete_document_button.text",
            icon_key="delete-file",
            tooltip="delete_document_button.tooltip",
            statustip="delete_document_button.statustip",
            enabled=False,
        )
        self.delete_document_button.clicked.connect(self.delete_current_document)

        # Export document action
        self.export_document_button: QToolButton = buttons.main_menu_button(
            self,
            text="export_button.text",
            icon_key="export",
            tooltip="export_button.tooltip",
            statustip="export_button.statustip",
            enabled=False,
        )
        self.export_document_button.clicked.connect(
            lambda: ExportDialog.create_dialog(self._controller)
        )

        # Add the buttons to the document menu widget
        document_menu: QWidget = buttons.button_group(
            [
                self.add_document_button,
                self.delete_document_button,
                self.export_document_button,
            ],
            "main_menu.button_group.document",
        )
        tab_layout.addWidget(document_menu)
        tab_layout.addWidget(buttons.get_separator(vertical=True))

        # ---------
        # Clipboard menu
        # ---------
        # Cut action
        self.cut_button: QToolButton = buttons.main_menu_button(
            self,
            text="cut_button.text",
            icon_key="clipboard-cut",
            tooltip="cut_button.tooltip",
            statustip="cut_button.statustip",
            enabled=False,
        )
        self.cut_button.clicked.connect(Clipboard().cut)

        # Copy action
        self.copy_button: QToolButton = buttons.main_menu_button(
            self,
            text="copy_button.text",
            icon_key="clipboard-copy",
            tooltip="copy_button.tooltip",
            statustip="copy_button.statustip",
            enabled=False,
        )
        self.copy_button.clicked.connect(Clipboard().copy)

        # Paste action
        self.paste_button: QToolButton = buttons.main_menu_button(
            self,
            text="paste_button.text",
            icon_key="clipboard-paste",
            tooltip="paste_button.tooltip",
            statustip="paste_button.statustip",
            enabled=False,
        )
        self.paste_button.clicked.connect(Clipboard().paste)

        # Add the buttons to the clipboard menu widget
        clipboard_menu: QWidget = buttons.button_group(
            [self.cut_button, self.copy_button, self.paste_button],
            "main_menu.button_group.clipboard",
        )
        tab_layout.addWidget(clipboard_menu)
        tab_layout.addWidget(buttons.get_separator(vertical=True))

        # ---------
        # Action menu
        # ---------
        # Undo action
        self.undo_button: QToolButton = buttons.main_menu_button(
            self,
            text="undo_button.text",
            icon_key="undo",
            tooltip="undo_button.tooltip",
            statustip="undo_button.statustip",
            enabled=False,
            shortcut="Ctrl+Z",
        )
        self.undo_button.clicked.connect(self._controller.undo)

        # Redo action
        self.redo_button: QToolButton = buttons.main_menu_button(
            self,
            text="redo_button.text",
            icon_key="redo",
            tooltip="redo_button.tooltip",
            statustip="redo_button.statustip",
            enabled=False,
            shortcut="Ctrl+Y",
        )
        self.redo_button.clicked.connect(self._controller.redo)

        # Add the buttons to the action menu widget
        action_menu: QWidget = buttons.button_group(
            [self.undo_button, self.redo_button],
            "main_menu.button_group.action",
        )
        tab_layout.addWidget(action_menu)
        tab_layout.addWidget(buttons.get_separator(vertical=True))

        # ---------
        # Analysis
        # ---------
        self.impact_analysis_button: QToolButton = buttons.main_menu_button(
            self,
            text="impact_analysis.text",
            icon_key="impact-analysis",
            tooltip="impact_analysis.tooltip",
            statustip="impact_analysis.statustip",
            enabled=False,
        )
        self.impact_analysis_button.clicked.connect(
            lambda: ImpactAnalysisWindow.show_dialog(self, self._controller)
        )

        analysis_menu: QWidget = buttons.button_group(
            [self.impact_analysis_button],
            "main_menu.button_group.analysis",
        )
        tab_layout.addWidget(analysis_menu)
        tab_layout.addWidget(buttons.get_separator(vertical=True))

        # ---------
        # aplication
        # ---------
        # Settings action
        self.settings_button: QToolButton = buttons.main_menu_button(
            self,
            text="settings_button.text",
            icon_key="settings",
            tooltip="settings_button.tooltip",
            statustip="settings_button.statustip",
        )
        self.settings_button.clicked.connect(
            lambda: SettingsDialog.create_dialog(self._controller)
        )

        # Information action
        self.information_button: QToolButton = buttons.main_menu_button(
            self,
            text="information_button.text",
            icon_key="info",
            tooltip="information_button.tooltip",
            statustip="information_button.statustip",
        )
        self.information_button.clicked.connect(
            lambda: InformationDialog.create_dialog(controller=self._controller)
        )

        # Add the buttons to the aplication menu widget
        aplication_menu: QWidget = buttons.button_group(
            [self.settings_button, self.information_button],
            "main_menu.button_group.application",
        )

        tab_layout.addWidget(aplication_menu)

        # ---------------------------------------------

        # Spacer to justify content left
        tab_layout.addStretch()

        # Add the main tab widget to the tab widget
        main_tab.setLayout(tab_layout)
        self.tab_widget.addTab(main_tab, tab_name)

    # ----------------------------------------------------------------------
    # Method     : add_archetype_tab
    # Description: Add a tab to the tab widget for a given class of object
    #              archetypes.
    # Date       : 29/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def add_archetype_tab(
        self, type_name: str, object_archetypes_by_class: Dict[str, List[Object]]
    ) -> None:
        """
        Add a tab to the tab widget for a given type of object archetypes.

        :param type_name: Name of the type of object archetypes.
        :param object_archetypes_by_class: Dictionary with the object
            archetypes separated by class.
        """
        # Create the tab widget with a horizontal layout
        tab_widget: QWidget = QWidget()
        tab_layout: QHBoxLayout = QHBoxLayout()
        tab_widget.setObjectName("archetype_tab")

        # Create a list to store archetype buttons to create the group
        buttons_list: List[ArchetypeMenuButton] = []

        # Add the archetype widgets to the tab widget
        for object_class in object_archetypes_by_class.keys():
            # Create the archetype button
            archetype_button: ArchetypeMenuButton = ArchetypeMenuButton(
                self, object_class
            )

            # Set single button if there is only one archetype
            archetype_list: List[Object] = object_archetypes_by_class[object_class]

            if len(archetype_list) == 1:
                archetype_button.clicked.connect(
                    lambda action, archetype_id=archetype_list[
                        0
                    ].id: self.create_object_from_archetype(
                        archetype_id, self._state_manager.get_current_object()
                    )
                )
                archetype_button.single_archetype_mode(archetype_list[0])
            elif len(archetype_list) > 1:
                # NOTE: This could be achieved using 'InstantPopup' mode, but it
                #       is a visual design decision
                archetype_button.setPopupMode(
                    QToolButton.ToolButtonPopupMode.MenuButtonPopup
                )
                archetype_button.setMenu(
                    ArchetypesMenuDropdown(
                        controller=self._controller,
                        archetype_list=archetype_list,
                    )
                )
                archetype_button.clicked.connect(archetype_button.showMenu)

            # Add the archetype button to the archetype buttons dictionary
            self.archetype_buttons[object_class] = archetype_button

            # Add the archetype button to the buttons list
            buttons_list.append(archetype_button)

        # Create text code for button group and bar names
        tab_name_code: str = f"archetype.category.{type_name}"

        # Create the archetype button group
        archetype_menu: QWidget = buttons.archetype_button_group(buttons_list)
        tab_layout.addWidget(archetype_menu)

        # Set the tab widget layout as the main widget of the tab widget
        tab_widget.setLayout(tab_layout)
        tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.archetype_tabs.append(tab_widget)
        self.tab_widget.addTab(tab_widget, _(tab_name_code, alternative_text=type_name))

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
            - SAVE PROJECT -> update_on_save_project
            - OPEN PROJECT -> update_on_open_project
            - SELECT OBJECT -> update_on_select_object
            - STACK CHANGED -> update_on_stack_changed
            - REQUIRED SAVE ACTION -> update_on_required_save_action
            - CURRENT DOCUMENT CHANGED -> update_on_current_document_changed

            - CLIPBOARD CHANGED -> update_on_clipboard_changed
            - SELECT OBJECT -> update_on_clipboard_changed
            - STACK CHANGED -> update_on_clipboard_changed
            - ARCHETYPE REPOSITORY CHANGED -> update_on_archetype_repository_changed
        """
        SaveProjectEvent().connect(self.update_on_save_project)
        OpenProjectEvent().connect(self.update_on_open_project)
        SelectObjectEvent().connect(self.update_on_select_object)
        StackChangedEvent().connect(self.update_on_stack_changed)
        RequiredSaveActionEvent().connect(self.update_on_required_save_action)
        CurrentDocumentChangedEvent().connect(self.update_on_current_document_changed)

        # Events to update the clipboard buttons
        ClipboardChangedEvent().connect(self.update_on_clipboard_changed)
        SelectObjectEvent().connect(self.update_on_clipboard_changed)
        StackChangedEvent().connect(self.update_on_clipboard_changed)
        ArchetypeRepositoryChangedEvent().connect(
            self.update_on_archetype_repository_changed
        )

    # ======================================================================
    # Component update methods (triggered by PROTEUS application events)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_on_stack_changed
    # Description: Update the state of save, undo and redo buttons when the
    #              command stack changes.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_stack_changed(self) -> None:
        """
        Update the state of save, undo and redo buttons when the command
        stack changes, enabling or disabling them depending on the state.

        Triggered by: StackChangedEvent
        """
        can_undo: bool = self._controller.stack.canUndo()
        can_redo: bool = self._controller.stack.canRedo()

        self.undo_button.setEnabled(can_undo)
        self.redo_button.setEnabled(can_redo)

    # ----------------------------------------------------------------------
    # Method     : update_on_required_save_action
    # Description: Update the state of save button when a save action is
    #              required.
    # Date       : 09/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_required_save_action(self, unsaved_changes: bool) -> None:
        """
        Update the state of save button if save action is required.

        Triggered by: RequiredSaveActionEvent
        """
        self.save_button.setEnabled(unsaved_changes)

    # ----------------------------------------------------------------------
    # Method     : update_on_save_project
    # Description: Update the state of save button when a project is saved.
    # Date       : 09/08/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_save_project(self) -> None:
        """
        Update the state of save button when a project is saved.

        Triggered by: SaveProjectEvent
        """
        self.save_button.setEnabled(False)

    # ----------------------------------------------------------------------
    # Method     : update_on_select_object
    # Description: Update the state of the archetype buttons when an object
    #              is selected.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_select_object(self, selected_object_id: ProteusID) -> None:
        """
        Update the state of the archetype buttons when an object is
        selected, enabling or disabling them depending on the accepted
        children of the selected object.

        Triggered by: SelectObjectEvent

        :param selected_object_id: ID of the selected object.
        """

        # If the selected object is None, disable all the archetype buttons
        if selected_object_id is None or selected_object_id == "":
            button: ArchetypeMenuButton = None
            for button in self.archetype_buttons.values():
                button.setEnabled(False)

            # Disable store_object_archetype_button
            if self.store_object_archetype_button:
                self.store_object_archetype_button.setEnabled(False)

        # If the selected object is not None, enable the archetype buttons
        # that are accepted children of the selected object
        else:
            # Get the selected object and its accepted children
            selected_object: Object = self._controller.get_element(selected_object_id)

            # If selected object exists, enable store_object_archetype_button
            if self.store_object_archetype_button:
                self.store_object_archetype_button.setEnabled(True)

            # Iterate over the archetype buttons
            for archetype_menu_button in self.archetype_buttons.values():

                # Handle single archetype buttons
                if archetype_menu_button.contains_only_one_archetype:
                    archetype_is_accepted: bool = selected_object.accept_descendant(
                        archetype_menu_button.archetype
                    )
                    archetype_menu_button.setEnabled(archetype_is_accepted)
                else:
                    # Get the menu of the archetype button
                    archetype_menu: ArchetypesMenuDropdown = (
                        archetype_menu_button.menu()
                    )

                    # Iterate over the archetype list and check at least one
                    # archetype is accepted by the selected object
                    enable: bool = False
                    for archetype in archetype_menu._archetype_list:

                        archetype_is_accepted: bool = selected_object.accept_descendant(
                            archetype
                        )

                        # Enable or disable the archetype button
                        if archetype_is_accepted:
                            archetype_menu.actions[archetype.id].setEnabled(True)
                        else:
                            archetype_menu.actions[archetype.id].setEnabled(False)

                        enable = enable or archetype_is_accepted

                    # Enable or disable the archetype button
                    archetype_menu_button.setEnabled(enable)

    # ----------------------------------------------------------------------
    # Method     : update_on_clipboard_changed
    # Description: Update the state of the clipboard buttons when the
    #              clipboard changes.
    # Date       : 31/07/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_clipboard_changed(self) -> None:
        """
        Update the state of the clipboard buttons when the clipboard
        changes, enabling or disabling them depending on the state.

        Triggered by: ClipboardChangedEvent, SelectObjectEvent, StackChangedEvent
        """
        # Triggered by stack changed event to prevent inconsistencies when
        # undo or redo actions are performed
        self.cut_button.setEnabled(Clipboard().can_cut_and_copy())
        self.copy_button.setEnabled(Clipboard().can_cut_and_copy())
        self.paste_button.setEnabled(Clipboard().can_paste())

    # ----------------------------------------------------------------------
    # Method     : update_on_open_project
    # Description: Enable the project properties and add document buttons
    #              when a project is opened.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_open_project(self) -> None:
        """
        Enable the project properties and add document buttons when a
        project is opened.

        Triggered by: OpenProjectEvent
        """
        self.project_properties_button.setEnabled(True)
        self.add_document_button.setEnabled(True)
        self.impact_analysis_button.setEnabled(True)

    # ----------------------------------------------------------------------
    # Method     : update_on_current_document_changed
    # Description: Update the state of the document buttons when the
    #              current document changes.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_on_current_document_changed(self, document_id: ProteusID) -> None:
        """
        Update the state of the document buttons when the current document
        changes, enabling or disabling them depending on the state.

        Triggered by: CurrentDocumentChangedEvent

        :param document_id: ID of the current document.
        """
        # Store if there is a document open
        is_document_open: bool = document_id is not None and document_id != ""

        self.delete_document_button.setEnabled(is_document_open)
        self.export_document_button.setEnabled(is_document_open)
        self.impact_analysis_button.setEnabled(is_document_open)

        if self.store_document_archetype_button:
            self.store_document_archetype_button.setEnabled(is_document_open)

        # Call update_on_select_object to update the archetype buttons
        if document_id == self._state_manager.get_current_document():
            current_object_id = self._state_manager.get_current_object()
            self.update_on_select_object(current_object_id)

    # ---------------------------------------------------------------------
    # Method     : update_on_archetype_repository_changed
    # Description: Update the archetype tabs when the archetype repository
    #              changes.
    # Date       : 30/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def update_on_archetype_repository_changed(self) -> None:
        """
        Update the archetype tabs when the archetype repository changes.
        """
        # Remove all the archetype tabs
        for tab in self.archetype_tabs:
            self.tab_widget.removeTab(self.tab_widget.indexOf(tab))
            tab.deleteLater()

        # Clear archetype buttons dictionary
        self.archetype_buttons.clear()

        # Clear the archetype tabs list
        self.archetype_tabs.clear()

        # Get the object archetypes
        object_archetypes_dict: Dict[str, Dict[str, List[Object]]] = (
            self._controller.get_first_level_object_archetypes()
        )

        # Create a tab for each type of object archetypes
        for type_name in object_archetypes_dict.keys():
            self.add_archetype_tab(type_name, object_archetypes_dict[type_name])

    # ======================================================================
    # Component slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_object_from_archetype
    # Description: Create a new object from the provided archetype and parent.
    # Date       : 11/12/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_object_from_archetype(self, archetype_id: ProteusID, parent_id: ProteusID) -> None:
        """
        Create a new object from the provided archetype and parent.

        :param archetype_id: The archetype id to create the object from.
        :param parent_id: The parent id to create the object from.
        """
        self._controller.create_object(archetype_id, parent_id)

        if Config().app_settings.edit_on_clone:
            if self._state_manager.last_cloned_archetype is not None:
                PropertyDialog.create_dialog(
                    self._controller,
                    self._state_manager.last_cloned_archetype,
                    True,
                )

    # ----------------------------------------------------------------------
    # Method     : open_project
    # Description: Manage the open project action, open a project using a
    #              file dialog and loads it.
    # Date       : 16/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def open_project(self) -> None:
        """
        Manage the open project action, open a project using a file dialog
        and loads it. If there is already a project open with unsaved
        changes, ask the user if he wants to save them before opening the
        new project.
        """
        # Open the file dialog
        # getOpenFileName returns a tuple where the first element is the
        # selected file path
        project_file_path: str = QFileDialog.getOpenFileName(
            None, _("main_menu.open_project.caption"), "", filter=PROJECT_FILE_NAME
        )[0]

        # If a directory was selected, check if there is already a project
        # open with unsaved changes and ask the user if he wants to save
        # them before opening the new project
        if project_file_path:
            # Check unsaved changes ---------------------
            # Check if the project has unsaved changes
            unsaved_changes: bool = not self._controller.stack.isClean()

            # Workaround to check when non undoable actions were not saved
            save_button_enabled: bool = False
            try:
                save_button_enabled = self.save_button.isEnabled()
            except AttributeError:
                pass

            # Unsaved changes confirmation dialog ---------------------
            if unsaved_changes or save_button_enabled:
                # TODO: This could be implemented using base_dialog.MessageBox but it
                # does not support connecting slots to buttons signals. Refactor MessageBox
                # to support this kind of scenarios??

                # Show a confirmation dialog
                confirmation_dialog = QMessageBox()
                confirmation_dialog.setIcon(QMessageBox.Icon.Warning)
                proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
                confirmation_dialog.setWindowIcon(proteus_icon)
                confirmation_dialog.setWindowTitle(
                    _("main_menu.open_project.save.title")
                )
                confirmation_dialog.setText(_("main_menu.open_project.save.text"))
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
                # Connect save_project method to the yes button
                confirmation_dialog.button(
                    QMessageBox.StandardButton.Yes
                ).clicked.connect(self.save_project)
                confirmation_dialog.exec()

            # Project load ---------------------
            try:
                directory_path = Path(project_file_path).parent
                self._controller.load_project(project_path=directory_path.as_posix())
                read_state_from_file(self._controller)
            except Exception as e:
                log.error(f"Error loading project: {e}")
                informative_text: str = str(e)

                tb: str = "".join(traceback.format_tb(e.__traceback__))
                log.error(tb)

                # Show an error message dialog
                MessageBox.critical(
                    _("main_menu.open_project.error.title"),
                    _("main_menu.open_project.error.text"),
                    informative_text,
                )

    # ----------------------------------------------------------------------
    # Method     : save_project
    # Description: Manage the save project action, save the current project.
    # Date       : 02/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_project(self) -> None:
        """
        Manage the save project action, save the current project.
        """
        self._controller.save_project()

        # Write the state to a file
        write_state_to_file()

    # ----------------------------------------------------------------------
    # Method     : delete_current_document
    # Description: Manage the delete current document action, delete the
    #              current document.
    # Date       : 06/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def delete_current_document(self) -> None:
        """
        Manage the delete current document action, delete the current
        document. Use a confirmation dialog to confirm the action.
        """
        # Get the current document
        document_id: ProteusID = self._state_manager.get_current_document()

        # Assert that the current document is not None
        assert (
            document_id is not None and document_id != ""
        ), "Current document is None or empty"

        # Create the delete dialog
        DeleteDialog.create_dialog(
            element_id=document_id,
            is_document=True,
            controller=self._controller,
        )

    # ==========================================================================
    # Overriden methods
    # ==========================================================================

    # ----------------------------------------------------------------------
    # Method     : resizeEvent
    # Description: Set the fixed height of the component.
    # Date       : 01/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def resizeEvent(self, event):
        """
        Overriden in order to prevent resizing the component vertically.
        """
        # Set the fixed height
        self.setFixedHeight(event.size().height())
        return super().resizeEvent(event)
