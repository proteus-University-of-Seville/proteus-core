# ==========================================================================
# File: settings_dialog.py
# Description: PyQT6 settings dialog component for the PROTEUS application
# Date: 18/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List
from pathlib import Path
from dataclasses import replace
from copy import deepcopy
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QWidget,
    QPushButton,
    QFileDialog,
)


# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.application.spellcheck import SpellCheckerWrapper
from proteus.application.configuration.config import Config
from proteus.application.configuration.app_settings import DEFAULT_MCP_HOST
from proteus.application.configuration.mcp_client_config import (
    write_mcp_client_config,
)
from proteus.application.state.manager import StateManager
from proteus.application.configuration.profile_settings import (
    ProfileSettings,
    ProfileBasicMetadata,
)
from proteus.controller.command_stack import Controller
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.themes import Themes
from proteus.application.resources.themes import ThemeService
from proteus.application.resources.translator import Translator, translate as _
from proteus.views.buttons import get_separator
from proteus.views.forms.directory_edit import DirectoryEdit
from proteus.views.forms.style_helpers import set_styled_property
from proteus.views.components.dialogs.base_dialogs import ProteusDialog, MessageBox


# Module configuration
log = logging.getLogger(__name__)

# Hosts that only accept connections from this machine. Any other host
# exposes the MCP server to the network, so the dialog warns about it.
LOCAL_MCP_HOSTS: List[str] = ["127.0.0.1", "localhost", "::1"]

# Valid range for the MCP server port (non privileged ports)
MIN_MCP_PORT: int = 1024
MAX_MCP_PORT: int = 65535


# --------------------------------------------------------------------------
# Class: SettingsDialog
# Description: PyQT6 settings dialog component for the PROTEUS application
# Date: 18/03/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SettingsDialog(ProteusDialog):
    """
    Settings dialog component class for the PROTEUS application. It provides a
    dialog form to change the application settings.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 18/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Create properties to store the new document data.
        """
        super(SettingsDialog, self).__init__(*args, **kwargs)

        # Settings edit widgets
        self.language_combo: QComboBox = None
        self.spellchecker_combo: QComboBox = None
        self.default_view_combo: QComboBox = None

        self.profile_combo: QComboBox = None
        self.custom_profile_edit: DirectoryEdit = None
        self.use_custom_profile_checkbox: QCheckBox = None

        self.open_project_on_startup_checkbox: QCheckBox = None
        self.edit_on_clone_checkbox: QCheckBox = None

        self.theme_combo: QComboBox = None

        self.developer_features_checkbox: QCheckBox = None
        self.xslt_debug_mode_checkbox: QCheckBox = None

        self.mcp_enabled_checkbox: QCheckBox = None
        self.mcp_host_edit: QLineEdit = None
        self.mcp_port_spinbox: QSpinBox = None
        self.mcp_client_config_button: QPushButton = None

        # Tabs
        self.tab_widget: QTabWidget = None
        self.general_tab: QWidget = None
        self.profile_tab: QWidget = None
        self.advanced_tab: QWidget = None

        # Description labels
        self.profile_description_label: QLabel = None
        self.view_description_label: QLabel = None

        # Warning message labels
        self.mcp_host_warning_label: QLabel = None

        # Error message labels
        self.error_profile_label: QLabel = None
        self.error_mcp_label: QLabel = None

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component
    # Date       : 18/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        # -------------------------------------------
        # Component general setup
        # -------------------------------------------
        # Set the dialog title
        self.setWindowTitle(_("settings_dialog.title"))

        # Set window icon
        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

        # Connect the buttons to the slots
        self.accept_button.setText(_("dialog.save_button"))
        self.accept_button.clicked.connect(self.save_button_clicked)

        # Setting message label
        setting_info_label: QLabel = QLabel(_("settings_dialog.info.label"))
        setting_info_label.setObjectName("setting_info_label")

        # -------------------------------------------
        # Layouts
        # -------------------------------------------
        layout: QVBoxLayout = QVBoxLayout()

        # Specific settings group boxes
        language_box: QGroupBox = self.create_language_box()
        appearance_box: QGroupBox = self.create_appearance_box()
        profile_box: QGroupBox = self.create_profile_box()
        default_view_box: QGroupBox = self.create_default_view_box()
        app_box: QGroupBox = self.create_app_box()
        developer_box: QGroupBox = self.create_developer_box()
        mcp_box: QGroupBox = self.create_mcp_box()

        # Tabs ---------------------------------------------------
        self.general_tab = self._create_tab([language_box, appearance_box, app_box])
        self.profile_tab = self._create_tab([profile_box, default_view_box])
        self.advanced_tab = self._create_tab([developer_box, mcp_box])

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.general_tab, _("settings_dialog.tab.general"))
        self.tab_widget.addTab(self.profile_tab, _("settings_dialog.tab.profile"))
        self.tab_widget.addTab(self.advanced_tab, _("settings_dialog.tab.advanced"))

        # Add the widgets to the layout
        layout.addWidget(setting_info_label)
        layout.addWidget(self.tab_widget)

        self.set_content_layout(layout)

    # ======================================================================
    # Layouts methods (create the component sub layouts)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_language_box
    # Description: Create the language group box
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_language_box(self) -> QGroupBox:
        """
        Create the language group box that contains the language combo box.

        Available languages are obtained from the translator instance.
        """
        # Language layout
        language_layout: QVBoxLayout = QVBoxLayout()

        # Language combo box --------------------------------------
        # Get available languages from translator instance
        languages: List[str] = Translator().available_languages

        # Create a combo box with the available views
        self.language_combo: QComboBox = QComboBox()

        for lang in languages:
            self.language_combo.addItem(
                _(f"settings.language.{lang}", alternative_text=lang),
                lang,
            )
            self.language_combo.setItemIcon(
                self.language_combo.count() - 1,
                Icons().icon(ProteusIconType.App, lang),
            )

        # Set the current language
        current_lang: str = Config().app_settings_copy.language

        assert (
            current_lang is not None or current_lang == ""
        ), "Error getting current language from configuration"

        index: int = self.language_combo.findData(current_lang)
        self.language_combo.setCurrentIndex(index)

        # Add the widgets to the layout
        language_layout.addWidget(self.language_combo)

        # SpellChecker combobox --------------------------------------
        spellchecker_label: QLabel = QLabel(_("settings_dialog.spellchecker.label"))
        self.spellchecker_combo: QComboBox = QComboBox()

        # Add first item that allows deactivation of the spellchecker
        self.spellchecker_combo.addItem(_("spellcheck.deactivate"), "")

        # Add the available languages
        for slang in SpellCheckerWrapper.list_available_languages():
            self.spellchecker_combo.addItem(
                _(f"spellcheck.language.{slang}", alternative_text=slang), slang
            )

        # Set the current spellcheck language
        current_spellchecker_lang: str = (
            Config().app_settings_copy.spellchecker_language
        )

        # Handle the case when the spellchecker is deactivated
        if current_spellchecker_lang is None or current_spellchecker_lang == "":
            current_spellchecker_lang = ""
            self.spellchecker_combo.setCurrentIndex(0)
        else:
            index: int = self.spellchecker_combo.findData(current_spellchecker_lang)
            self.spellchecker_combo.setCurrentIndex(index)

        # Add the widgets to the layout
        language_layout.addWidget(spellchecker_label)
        language_layout.addWidget(self.spellchecker_combo)

        # Group box -----------------------------------------------
        language_group: QGroupBox = QGroupBox(_("settings_dialog.language.group"))
        language_group.setLayout(language_layout)

        return language_group

    # ---------------------------------------------------------------------
    # Method     : create_profile_box
    # Description: Create the profile group box
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def create_profile_box(self) -> QGroupBox:
        """
        Create the repository group box that contains the profile settings
        (default or custom profile path)
        """
        profile_layout: QVBoxLayout = QVBoxLayout()

        # Profile info --------------------------------------------
        custom_profile_path: Path = Config().app_settings_copy.custom_profile_path
        custom_profile_dir_str: str
        if custom_profile_path is None:
            custom_profile_dir_str = ""
        else:
            custom_profile_dir_str = custom_profile_path.as_posix()

        using_default_profile: bool = Config().app_settings_copy.using_default_profile

        # Profiles combo box --------------------------------------
        self.profile_combo: QComboBox = QComboBox()

        profile_id: str
        profile_metadata: ProfileBasicMetadata
        for profile_id, profile_metadata in Config().listed_profiles.items():
            self.profile_combo.addItem(profile_metadata.name, profile_id)
            self.profile_combo.setItemIcon(
                self.profile_combo.count() - 1,
                QIcon(profile_metadata.image.as_posix()),
            )

        self.profile_combo.setCurrentIndex(
            self.profile_combo.findData(Config().app_settings_copy.selected_profile)
        )

        self.profile_combo.setEnabled(using_default_profile)

        # Description label
        self.profile_description_label: QLabel = QLabel()
        self.profile_description_label.setWordWrap(True)
        set_styled_property(
            self.profile_description_label, "descriptionState", "filled"
        )

        # Update the description label when the combo box changes
        # NOTE: Profile metadata is never internationalized
        self.profile_combo.currentIndexChanged.connect(
            lambda: self._update_profile_description_label()
        )
        self.profile_combo.currentIndexChanged.emit(self.profile_combo.currentIndex())

        # Default profile checkbox --------------------------------
        self.use_custom_profile_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.default_profile.checkbox")
        )
        self.use_custom_profile_checkbox.setChecked(not using_default_profile)

        # Directory edit -------------------------------------
        self.custom_profile_edit: DirectoryEdit = DirectoryEdit()
        self.custom_profile_edit.setEnabled(not using_default_profile)
        self.custom_profile_edit.setDirectory(custom_profile_dir_str)

        # Error message label -------------------------------------
        self.error_profile_label: QLabel = QLabel()
        self.error_profile_label.setObjectName("error_label")
        self.error_profile_label.setWordWrap(True)
        self.error_profile_label.setHidden(True)

        # Connect checkbox signal to the directory edit and combo setEnabled
        # state = 2 is checked, state = 0 is unchecked
        self.use_custom_profile_checkbox.stateChanged.connect(
            lambda state: self.custom_profile_edit.setEnabled(state == 2)
        )
        self.use_custom_profile_checkbox.stateChanged.connect(
            lambda state: self.profile_combo.setEnabled(state == 0)
        )

        # Add the widgets to the layout ---------------------------
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.profile_description_label)
        profile_layout.addWidget(get_separator())
        profile_layout.addWidget(self.use_custom_profile_checkbox)
        profile_layout.addWidget(self.custom_profile_edit)
        profile_layout.addWidget(self.error_profile_label)

        # Group box
        profile_group: QGroupBox = QGroupBox(_("settings_dialog.default_profile.group"))
        profile_group.setLayout(profile_layout)

        return profile_group

    # ---------------------------------------------------------------------
    # Method     : create_default_view_box
    # Description: Create the default view group box
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def create_default_view_box(self) -> QGroupBox:
        """
        Create the default view group box that contains the selected default
        view among the views of the profile.
        """
        # View layout
        layout: QVBoxLayout = QVBoxLayout()

        # Default view -------------------------------------
        self.default_view_combo: QComboBox = QComboBox()
        for view_name in self._controller.get_available_xslt():
            self.default_view_combo.addItem(
                _(f"xslt_templates.{view_name}", alternative_text=view_name),
                view_name,
            )

        # Set the current view
        current_default_view: str = Config().app_settings_copy.default_view
        index: int = self.default_view_combo.findData(current_default_view)
        self.default_view_combo.setCurrentIndex(index)

        # Description label
        self.view_description_label: QLabel = QLabel()
        self.view_description_label.setWordWrap(True)

        # Update the description label when the combo box changes
        self.default_view_combo.currentIndexChanged.connect(
            lambda: self._update_xslt_template_description_label()
        )
        self.default_view_combo.currentIndexChanged.emit(
            self.default_view_combo.currentIndex()
        )

        # Add the widgets to the layout
        layout.addWidget(self.default_view_combo)
        layout.addWidget(self.view_description_label)

        # Group box
        group: QGroupBox = QGroupBox(_("settings_dialog.default_view.group"))
        group.setLayout(layout)

        return group

    # ---------------------------------------------------------------------
    # Method     : create_appearance_box
    # Description: Create the appearance (theme) group box
    # Date       : 03/05/2026
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def create_appearance_box(self) -> QGroupBox:
        """
        Create the Appearance group box that lets the user pick a theme.

        Themes are discovered by the Themes singleton from
        resources/themes/ at startup. Selecting a different theme persists
        to proteus.ini and is applied live on save (no restart required).
        """
        appearance_layout: QVBoxLayout = QVBoxLayout()

        theme_label: QLabel = QLabel(_("settings_dialog.theme.label"))
        self.theme_combo: QComboBox = QComboBox()

        themes = Themes().available_themes
        for theme_key, metadata in themes.items():
            display_name: str = _(
                f"settings_dialog.theme.{theme_key}",
                alternative_text=metadata.name,
            )
            self.theme_combo.addItem(display_name, theme_key)

        # Pre-select the active theme. Use the value from app_settings_copy
        # so re-opening the dialog reflects the user's pending choice.
        current_theme: str = Config().app_settings_copy.theme
        index = self.theme_combo.findData(current_theme)
        if index < 0 and Themes().current_theme is not None:
            # Fall back to whichever theme actually loaded.
            index = self.theme_combo.findData(Themes().current_theme.key)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        # Disable the combo if no themes were discovered (defensive).
        if self.theme_combo.count() == 0:
            self.theme_combo.setEnabled(False)
            self.theme_combo.addItem(_("settings_dialog.theme.none_available"), "")

        appearance_layout.addWidget(theme_label)
        appearance_layout.addWidget(self.theme_combo)

        appearance_group: QGroupBox = QGroupBox(_("settings_dialog.appearance.group"))
        appearance_group.setLayout(appearance_layout)

        return appearance_group

    # ---------------------------------------------------------------------
    # Method     : create_app_box
    # Description: Create the startup group box
    # Date       : 13/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def create_app_box(self) -> QGroupBox:
        """
        Create the app group box that contains the open project on startup checkbox
        and edit on clone checkbox.
        """
        # Startup layout
        app_layout: QVBoxLayout = QVBoxLayout()

        # Open project on startup -------------------------------------
        self.open_project_on_startup_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.open_project_on_startup.checkbox")
        )

        # Add tooltip
        self.open_project_on_startup_checkbox.setToolTip(
            _("settings_dialog.open_project_on_startup.tooltip")
        )

        # Set the current value
        self.open_project_on_startup_checkbox.setChecked(
            Config().app_settings_copy.open_project_on_startup
        )

        # Add the widgets to the layout
        app_layout.addWidget(self.open_project_on_startup_checkbox)

        # Edit on clone -------------------------------------
        self.edit_on_clone_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.edit_on_clone.checkbox")
        )

        # Add tooltip
        self.edit_on_clone_checkbox.setToolTip(
            _("settings_dialog.edit_on_clone.tooltip")
        )

        # Set the current value
        self.edit_on_clone_checkbox.setChecked(
            Config().app_settings_copy.edit_on_clone
        )

        # Add the widgets to the layout
        app_layout.addWidget(self.edit_on_clone_checkbox)

        # Group box -----------------------------------------------
        startup_group: QGroupBox = QGroupBox(_("settings_dialog.app.group"))
        startup_group.setLayout(app_layout)

        return startup_group

    # ---------------------------------------------------------------------
    # Method     : create_developer_box
    # Description: Create the developer settings group box
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ---------------------------------------------------------------------
    def create_developer_box(self) -> QGroupBox:
        """
        Create the developer group box that contains the developer features
        checkbox and the XSLT debug mode checkbox.
        """
        developer_layout: QVBoxLayout = QVBoxLayout()

        # Developer features -------------------------------------
        self.developer_features_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.developer_features.checkbox")
        )
        self.developer_features_checkbox.setToolTip(
            _("settings_dialog.developer_features.tooltip")
        )
        self.developer_features_checkbox.setChecked(
            Config().app_settings_copy.developer_features
        )

        # XSLT debug mode ----------------------------------------
        self.xslt_debug_mode_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.xslt_debug_mode.checkbox")
        )
        self.xslt_debug_mode_checkbox.setToolTip(
            _("settings_dialog.xslt_debug_mode.tooltip")
        )
        self.xslt_debug_mode_checkbox.setChecked(
            Config().app_settings_copy.xslt_debug_mode
        )

        # Add the widgets to the layout
        developer_layout.addWidget(self.developer_features_checkbox)
        developer_layout.addWidget(self.xslt_debug_mode_checkbox)

        # Group box -----------------------------------------------
        developer_group: QGroupBox = QGroupBox(_("settings_dialog.developer.group"))
        developer_group.setLayout(developer_layout)

        return developer_group

    # ---------------------------------------------------------------------
    # Method     : create_mcp_box
    # Description: Create the embedded MCP server group box
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ---------------------------------------------------------------------
    def create_mcp_box(self) -> QGroupBox:
        """
        Create the MCP group box that contains the embedded MCP server
        settings (enabled, host and port). Host and port are only enabled
        when the server is enabled.
        """
        mcp_layout: QVBoxLayout = QVBoxLayout()

        app_settings = Config().app_settings_copy

        # Enabled checkbox ---------------------------------------
        self.mcp_enabled_checkbox: QCheckBox = QCheckBox(
            _("settings_dialog.mcp.enabled.checkbox")
        )
        self.mcp_enabled_checkbox.setToolTip(_("settings_dialog.mcp.enabled.tooltip"))
        self.mcp_enabled_checkbox.setChecked(app_settings.mcp_server_enabled)

        # Host edit ----------------------------------------------
        self.mcp_host_edit: QLineEdit = QLineEdit()
        self.mcp_host_edit.setText(app_settings.mcp_server_host)
        self.mcp_host_edit.setPlaceholderText(DEFAULT_MCP_HOST)

        # Port spin box ------------------------------------------
        self.mcp_port_spinbox: QSpinBox = QSpinBox()
        self.mcp_port_spinbox.setRange(MIN_MCP_PORT, MAX_MCP_PORT)
        self.mcp_port_spinbox.setValue(app_settings.mcp_server_port)

        host_port_layout: QFormLayout = QFormLayout()
        host_port_layout.addRow(_("settings_dialog.mcp.host.label"), self.mcp_host_edit)
        host_port_layout.addRow(
            _("settings_dialog.mcp.port.label"), self.mcp_port_spinbox
        )

        # Client configuration button ----------------------------
        self.mcp_client_config_button: QPushButton = QPushButton(
            _("settings_dialog.mcp.client_config.button")
        )
        self.mcp_client_config_button.setToolTip(
            _("settings_dialog.mcp.client_config.tooltip")
        )
        self.mcp_client_config_button.clicked.connect(
            self.mcp_client_config_button_clicked
        )

        # Warning message label (non local host) -----------------
        self.mcp_host_warning_label: QLabel = QLabel(
            _("settings_dialog.mcp.host.warning")
        )
        self.mcp_host_warning_label.setObjectName("error_label")
        self.mcp_host_warning_label.setWordWrap(True)

        # Error message label ------------------------------------
        self.error_mcp_label: QLabel = QLabel()
        self.error_mcp_label.setObjectName("error_label")
        self.error_mcp_label.setWordWrap(True)
        self.error_mcp_label.setHidden(True)

        # Connect signals to keep enabled state and warning updated
        self.mcp_enabled_checkbox.stateChanged.connect(
            lambda: self._update_mcp_widgets()
        )
        self.mcp_host_edit.textChanged.connect(lambda: self._update_mcp_widgets())
        self._update_mcp_widgets()

        # Add the widgets to the layout ---------------------------
        mcp_layout.addWidget(self.mcp_enabled_checkbox)
        mcp_layout.addLayout(host_port_layout)
        mcp_layout.addWidget(self.mcp_client_config_button)
        mcp_layout.addWidget(self.mcp_host_warning_label)
        mcp_layout.addWidget(self.error_mcp_label)

        # Group box -----------------------------------------------
        mcp_group: QGroupBox = QGroupBox(_("settings_dialog.mcp.group"))
        mcp_group.setLayout(mcp_layout)

        return mcp_group

    # ======================================================================
    # Validators
    # ======================================================================

    # ---------------------------------------------------------------------
    # Method     : validate_profile
    # Description: Validate the selected profile
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def validate_profile(self) -> bool:
        """
        Validate if the custom profile can be loaded from the selected path.

        :return: True if the profile can be loaded, False otherwise
        """
        using_custom_profile: bool = self.use_custom_profile_checkbox.isChecked()
        profile_path: str = self.custom_profile_edit.directory()

        # If it is using custom repository, check if it is correct
        if using_custom_profile:
            # Check if the path is empty
            if profile_path == "":
                self.error_profile_label.setText(
                    _("settings_dialog.error.profile.empty_path")
                )
                self.error_profile_label.setHidden(False)
                return False

            # Check if the path exists
            _profile_path: Path = Path(profile_path)
            if not _profile_path.exists():
                self.error_profile_label.setText(
                    _("settings_dialog.error.profile.invalid_path")
                )
                self.error_profile_label.setHidden(False)
                return False

            # Check if it is a valid profile using profile settings loader
            try:
                ProfileSettings.load(_profile_path)
            except Exception as e:
                log.error(
                    f"Error loading custom profile from path {_profile_path} error: {e}"
                )
                self.error_profile_label.setText(
                    _("settings_dialog.error.profile.invalid_profile", e)
                )
                self.error_profile_label.setHidden(False)
                return False

        # If we reach this point, there are no errors
        self.error_profile_label.setHidden(True)
        return True

    # ---------------------------------------------------------------------
    # Method     : validate_mcp
    # Description: Validate the embedded MCP server settings
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ---------------------------------------------------------------------
    def validate_mcp(self) -> bool:
        """
        Validate that the MCP server host is not empty when the server is
        enabled. The port is always valid because the spin box limits it.

        :return: True if the MCP settings are valid, False otherwise
        """
        if self.mcp_enabled_checkbox.isChecked() and not self._mcp_host():
            self.error_mcp_label.setText(_("settings_dialog.error.mcp.empty_host"))
            self.error_mcp_label.setHidden(False)
            return False

        self.error_mcp_label.setHidden(True)
        return True

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : save_button_clicked
    # Description: Save button clicked event handler
    # Date       : 18/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_button_clicked(self) -> None:
        """
        Manage the save button clicked event. It saves the current settings
        """
        # ---------------------
        # Validate settings
        # ---------------------
        valid_mcp: bool = self.validate_mcp()
        valid_profile: bool = self.validate_profile()

        # If there are errors, show the tab of the first one and do not
        # save the settings
        if not valid_profile:
            self.tab_widget.setCurrentWidget(self.profile_tab)
            return

        if not valid_mcp:
            self.tab_widget.setCurrentWidget(self.advanced_tab)
            return

        # ---------------------
        # Store validated settings
        # ---------------------

        config = Config()

        # Compare this save with the previously staged values, not only with
        # the boot-time settings snapshot.
        settings_before_save = config.app_settings_copy

        custom_profile_path: Path = (
            Path(self.custom_profile_edit.directory())
            if self.custom_profile_edit.directory()
            else None
        )

        # Resolve the chosen theme. If the combo holds the empty-fallback
        # entry (no themes discovered) keep the existing value.
        chosen_theme: str = (
            self.theme_combo.currentData()
            if self.theme_combo is not None and self.theme_combo.currentData()
            else config.app_settings_copy.theme
        )

        staged_settings = config.app_settings_copy.clone(
            language=self.language_combo.currentData(),
            spellchecker_language=self.spellchecker_combo.currentData(),
            default_view=self.default_view_combo.currentData(),
            selected_profile=self.profile_combo.currentData(),
            using_default_profile=(not self.use_custom_profile_checkbox.isChecked()),
            custom_profile_path=custom_profile_path,
            open_project_on_startup=self.open_project_on_startup_checkbox.isChecked(),
            edit_on_clone=self.edit_on_clone_checkbox.isChecked(),
            theme=chosen_theme,
            xslt_debug_mode=self.xslt_debug_mode_checkbox.isChecked(),
            developer_features=self.developer_features_checkbox.isChecked(),
            mcp_server_enabled=self.mcp_enabled_checkbox.isChecked(),
            mcp_server_host=self._mcp_host() or DEFAULT_MCP_HOST,
            mcp_server_port=self.mcp_port_spinbox.value(),
        )

        # Config.app_settings is a boot-time snapshot. Compare with the
        # currently applied theme so successive saves can switch both ways.
        current_theme_key: str | None = (
            Themes().current_theme.key
            if Themes().current_theme is not None
            else None
        )
        theme_changed: bool = (
            current_theme_key is not None and chosen_theme != current_theme_key
        )
        if theme_changed and not ThemeService().apply_theme(chosen_theme):
            MessageBox.warning(
                _("settings_dialog.error.theme.title"),
                _("settings_dialog.error.theme.text"),
            )
            return

        # AppSettings.save mutates its shared ConfigParser before writing the
        # file, so restore that snapshot if the write fails.
        previous_parser = deepcopy(settings_before_save.config_parser)
        try:
            staged_settings.save()
        except Exception as exc:
            log.error("Could not save settings: %s", exc)
            config.app_settings.config_parser = previous_parser
            settings_before_save.config_parser = previous_parser
            if theme_changed and current_theme_key is not None:
                ThemeService().apply_theme(current_theme_key)
            MessageBox.warning(
                _("settings_dialog.error.save.title"),
                _("settings_dialog.error.save.text"),
            )
            return

        config.app_settings_copy = staged_settings

        # Exclude theme from both comparisons: other settings may still
        # require a restart, but an unchanged save must not warn again.
        settings_excluding_theme = staged_settings.clone(
            theme=config.app_settings.theme
        )
        restart_needed: bool = config.app_settings != settings_excluding_theme
        save_changed_settings: bool = replace(
            settings_before_save, theme=""
        ) != replace(staged_settings, theme="")
        if restart_needed and save_changed_settings:
            MessageBox.warning(
                _("settings_dialog_warning.title"),
                _("settings_dialog_warning.text"),
            )

        # Close the form window
        self.close()
        self.deleteLater()

    # ----------------------------------------------------------------------
    # Method     : mcp_client_config_button_clicked
    # Description: Generate .mcp.json button clicked event handler
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def mcp_client_config_button_clicked(self) -> None:
        """
        Ask for a directory and create or update its .mcp.json file with the
        PROTEUS MCP server entry, using the host and port in the dialog. The
        directory of the open project is suggested.
        """
        if not self.validate_mcp():
            return

        project_path: Path = StateManager().current_project_path
        start_directory: str = project_path.as_posix() if project_path else ""

        directory: str = QFileDialog.getExistingDirectory(
            self, _("settings_dialog.mcp.client_config.dialog"), start_directory
        )

        # Dialog cancelled
        if not directory:
            return

        try:
            config_path: Path = write_mcp_client_config(
                Path(directory), self._mcp_host(), self.mcp_port_spinbox.value()
            )
        except (ValueError, OSError) as e:
            log.error(f"Could not write the MCP client configuration: {e}")
            MessageBox.warning(
                _("settings_dialog.mcp.client_config.error.title"),
                _("settings_dialog.mcp.client_config.error.text"),
                str(e),
            )
            return

        MessageBox.information(
            _("settings_dialog.mcp.client_config.success.title"),
            _("settings_dialog.mcp.client_config.success.text", config_path.as_posix()),
        )


    # ======================================================================
    # Helper methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : _create_tab
    # Description: Create a tab page with the given group boxes.
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _create_tab(self, group_boxes: List[QGroupBox]) -> QWidget:
        """
        Create a tab page that stacks the given group boxes vertically,
        aligned to the top.
        """
        tab_layout: QVBoxLayout = QVBoxLayout()
        for group_box in group_boxes:
            tab_layout.addWidget(group_box)
        tab_layout.addStretch()

        tab: QWidget = QWidget()
        tab.setLayout(tab_layout)

        return tab

    # ----------------------------------------------------------------------
    # Method     : _mcp_host
    # Description: Return the MCP host typed by the user.
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _mcp_host(self) -> str:
        """
        Return the MCP host typed by the user without surrounding spaces.
        """
        return self.mcp_host_edit.text().strip()

    # ----------------------------------------------------------------------
    # Method     : _update_mcp_widgets
    # Description: Update the enabled state of the MCP widgets.
    # Date       : 21/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _update_mcp_widgets(self) -> None:
        """
        Enable host and port only when the MCP server is enabled, and show
        the warning when the server would accept connections from other
        machines.
        """
        enabled: bool = self.mcp_enabled_checkbox.isChecked()
        self.mcp_host_edit.setEnabled(enabled)
        self.mcp_port_spinbox.setEnabled(enabled)
        self.mcp_client_config_button.setEnabled(enabled)

        host: str = self._mcp_host()
        self.mcp_host_warning_label.setHidden(
            not enabled or host == "" or host.lower() in LOCAL_MCP_HOSTS
        )

    # ----------------------------------------------------------------------
    # Method     : _update_xslt_templtate_description_label
    # Description: Update the description label with the description.
    # Date       : 22/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _update_xslt_template_description_label(self) -> None:
        """
        Update the description label with the description found using the translation code
        and the combo box current data.
        """
        profile_id: str = self.default_view_combo.currentData()
        if profile_id:
            description: str = _(
                f"xslt_templates.description.{profile_id}", alternative_text=""
            )
            if description == "":
                set_styled_property(
                    self.view_description_label, "descriptionState", "empty"
                )
                self.view_description_label.setText(
                    _("settings_dialog.descriptions.empty")
                )
            else:
                set_styled_property(
                    self.view_description_label, "descriptionState", "filled"
                )
                self.view_description_label.setText(description)

    def _update_profile_description_label(self) -> None:
        """
        Update the profile description label with the description found using the translation code
        and the combo box current data.
        """
        profile_id: str = self.profile_combo.currentData()
        if profile_id:
            description: str = Config().listed_profiles[profile_id].description
            if description == "":
                set_styled_property(
                    self.profile_description_label, "descriptionState", "empty"
                )
                self.profile_description_label.setText(
                    _("settings_dialog.descriptions.empty")
                )
            else:
                set_styled_property(
                    self.profile_description_label, "descriptionState", "filled"
                )
                self.profile_description_label.setText(description)

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog
    # Description: Create a settings dialog and show it
    # Date       : 18/03/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(controller: Controller) -> "SettingsDialog":
        """
        Create a settings dialog and show it
        """
        dialog = SettingsDialog(controller=controller)
        dialog.exec()
        return dialog
