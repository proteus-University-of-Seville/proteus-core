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
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QGroupBox,
)


# --------------------------------------------------------------------------
# document specific imports
# --------------------------------------------------------------------------

from proteus.application.spellcheck import SpellCheckerWrapper
from proteus.application.configuration.config import Config
from proteus.application.configuration.profile_settings import (
    ProfileSettings,
    ProfileBasicMetadata,
)
from proteus.controller.command_stack import Controller
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.translator import Translator, translate as _
from proteus.views.buttons import get_separator
from proteus.views.forms.directory_edit import DirectoryEdit
from proteus.views.components.dialogs.base_dialogs import ProteusDialog, MessageBox


# Module configuration
log = logging.getLogger(__name__)


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

        # Description labels
        self.profile_description_label: QLabel = None
        self.view_description_label: QLabel = None

        # Error message labels
        self.error_profile_label: QLabel = None

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
        setting_info_label.setStyleSheet("font-weight: bold")

        # -------------------------------------------
        # Layouts
        # -------------------------------------------
        layout: QVBoxLayout = QVBoxLayout()

        # Specific settings group boxes
        language_box: QGroupBox = self.create_language_box()
        profile_box: QGroupBox = self.create_profile_box()
        profile_specific_settings: QGroupBox = (
            self.create_profile_specific_settings_box()
        )
        app_box: QGroupBox = self.create_app_box()

        # Add the widgets to the layout
        layout.addWidget(setting_info_label)
        layout.addWidget(language_box)
        layout.addWidget(app_box)
        layout.addWidget(profile_specific_settings)
        layout.addWidget(profile_box)
        layout.addStretch()

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
        self.profile_description_label.setStyleSheet("color: black; font-style: italic")

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
    # Method     : create_profile_specific_settings_box
    # Description: Create the profile specific settings group box
    # Date       : 25/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def create_profile_specific_settings_box(self) -> QGroupBox:
        """
        Create the profile specific settings group box that contains the
        the selected default view.
        """
        # View layout
        layout: QVBoxLayout = QVBoxLayout()

        # Default view -------------------------------------
        default_view_label: QLabel = QLabel(_("settings_dialog.default_view.label"))
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
        layout.addWidget(default_view_label)
        layout.addWidget(self.default_view_combo)
        layout.addWidget(self.view_description_label)

        # Group box
        group: QGroupBox = QGroupBox(_("settings_dialog.profile_settings.group"))
        group.setLayout(layout)

        return group

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
        valid_settings: bool = True
        valid_settings = self.validate_profile() and valid_settings

        # If there are errors, do not save the settings
        if not valid_settings:
            return

        # ---------------------
        # Store validated settings
        # ---------------------

        config = Config()

        custom_profile_path: Path = (
            Path(self.custom_profile_edit.directory())
            if self.custom_profile_edit.directory()
            else None
        )

        config.app_settings_copy = config.app_settings_copy.clone(
            language=self.language_combo.currentData(),
            spellchecker_language=self.spellchecker_combo.currentData(),
            default_view=self.default_view_combo.currentData(),
            selected_profile=self.profile_combo.currentData(),
            using_default_profile=(not self.use_custom_profile_checkbox.isChecked()),
            custom_profile_path=custom_profile_path,
            open_project_on_startup=self.open_project_on_startup_checkbox.isChecked(),
            edit_on_clone=self.edit_on_clone_checkbox.isChecked(),
        )

        # ---------------------
        # Save settings
        # ---------------------
        config.app_settings_copy.save()

        # Show warning dialog, the changes will be applied after restart
        # Avoid showing the warning dialog if the settings are the same as the
        # current loaded settings
        if config.app_settings != config.app_settings_copy:
            MessageBox.warning(
                _("settings_dialog_warning.title"),
                _("settings_dialog_warning.text"),
            )

        # Close the form window
        self.close()
        self.deleteLater()


    # ======================================================================
    # Helper methods
    # ======================================================================

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
                self.view_description_label.setStyleSheet(
                    "color: red; font-style: italic"
                )
                self.view_description_label.setText(
                    _("settings_dialog.descriptions.empty")
                )
            else:
                self.view_description_label.setStyleSheet(
                    "color: black; font-style: italic"
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
                self.profile_description_label.setStyleSheet(
                    "color: red; font-style: italic"
                )
                self.profile_description_label.setText(
                    _("settings_dialog.descriptions.empty")
                )
            else:
                self.profile_description_label.setStyleSheet(
                    "color: black; font-style: italic"
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
