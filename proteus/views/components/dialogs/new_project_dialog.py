# ==========================================================================
# File: new_project_dialog.py
# Description: PyQT6 new project component for the PROTEUS application
# Date: 28/05/2023
# Version: 0.2
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import List
from pathlib import Path
import os

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QWizard,
    QWizardPage,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import PROTEUS_NAME
from proteus.model.project import Project
from proteus.views.forms.directory_edit import DirectoryEdit
from proteus.views.forms.style_helpers import set_styled_property
from proteus.views.forms.validators import is_valid_folder_name
from proteus.views.components.abstract_component import ProteusComponent
from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _
from proteus.application.resources.icons import Icons, ProteusIconType



# --------------------------------------------------------------------------
# Class: NewProjectDialog
# Description: PyQT6 new project wizard dialog for the PROTEUS application
# Date: 01/05/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class NewProjectDialog(QWizard, ProteusComponent):
    """
    Wizard dialog for creating a new project in the PROTEUS application.
    Guides the user through the process of selecting an archetype, a path and a name for the project.
    """

    def __init__(self, *args, **kwargs):
        super(NewProjectDialog, self).__init__(*args, **kwargs)

        # Wizard configuration
        self.setWindowTitle(_("new_project_dialog.title"))

        proteus_icon = Icons().icon(ProteusIconType.App, "proteus_icon")
        self.setWindowIcon(proteus_icon)

        us_logo = Icons().icon(ProteusIconType.App, "US-digital")
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, us_logo.pixmap(64, 64))

        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)


        # Buttons translations
        self.setButtonText(
            QWizard.WizardButton.CancelButton, _("wizard_dialog.buttons.cancel")
        )
        self.setButtonText(
            QWizard.WizardButton.NextButton, _("wizard_dialog.buttons.next")
        )
        self.setButtonText(
            QWizard.WizardButton.FinishButton, _("wizard_dialog.buttons.finish")
        )
        self.setButtonText(
            QWizard.WizardButton.BackButton, _("wizard_dialog.buttons.back")
        )
        self.setButtonText(
            QWizard.WizardButton.HelpButton, _("wizard_dialog.buttons.help")
        )

        # Pages
        self.addPage(ArchetypePage(self._controller.get_project_archetypes()))
        self.addPage(PathPage())
        self.addPage(NamePage())

    def accept(self):
        if self.validateCurrentPage():
            project_archetypes: List[Project] = (
                self._controller.get_project_archetypes()
            )

            name = self.field("name")
            path = self.field("path")
            index = self.field("archetype")
            archetype = project_archetypes[index - 1].id

            super().accept()
            self._controller.create_project(archetype, name, path)

    @staticmethod
    def create_dialog(controller: Controller) -> "NewProjectDialog":
        dialog = NewProjectDialog(controller=controller)
        dialog.exec()
        return dialog


class ArchetypePage(QWizardPage):
    """
    Select an archetype for the new project in a combobox. If the project has
    a description, it will be displayed below the combobox.
    """

    def __init__(self, archetypes: List[Project], *args, **kwargs):
        super(ArchetypePage, self).__init__(*args, **kwargs)

        # Variables
        self.archetypes = archetypes

        # Set the title and subtitle
        self.setTitle(_("new_project_dialog.archetype.title"))
        self.setSubTitle(_("new_project_dialog.archetype.subtitle"))

        # Archetype Combobox
        self.archetype_combo = QComboBox()
        self.archetype_combo.addItem(_("new_project_dialog.archetype.select_archetype"), None)
        for archetype in archetypes:
            self.archetype_combo.addItem(archetype.get_property(PROTEUS_NAME).value, archetype.id)

        self.registerField("archetype*", self.archetype_combo)

        # Error label
        self.error_label = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)

        # Description label
        self.description_label = QLabel(_("new_project_dialog.archetype.description"))
        self.description_label.setWordWrap(True)

        self.description_container_label = QLabel()
        self.description_container_label.setWordWrap(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.archetype_combo)
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_container_label)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

        # Signals
        self.archetype_combo.currentIndexChanged.connect(self.update_description)

    def update_description(self):
        index = self.archetype_combo.currentIndex()
        if index > 0:
            # -1 ommits the default option
            archetype: Project = self.archetypes[index - 1]

            description_property = archetype.get_property("description")
            if description_property is not None:
                set_styled_property(
                    self.description_container_label, "descriptionState", "filled"
                )
                self.description_container_label.setText(description_property.value)
                return

        set_styled_property(
            self.description_container_label, "descriptionState", "empty"
        )
        self.description_container_label.setText(
            _("settings_dialog.descriptions.empty")
        )

        self.adjustSize()

    def validatePage(self):
        index = self.archetype_combo.currentIndex()
        if index == 0:
            self.error_label.setText(
                _("new_project_dialog.error.no_archetype_selected")
            )
            return False

        self.error_label.setText("")
        return True

    def cleanupPage(self) -> None:
        self.error_label.setText("")
        self.archetype_combo.setCurrentIndex(0)
        self.update_description()
        return super().cleanupPage()


class PathPage(QWizardPage):
    """
    Select a path for the new project using a DirectoryEdit widget (QLineEdit
    with a QFileDialog button).
    """

    def __init__(self, *args, **kwargs):
        super(PathPage, self).__init__(*args, **kwargs)

        # Set the title and subtitle
        self.setTitle(_("new_project_dialog.path.title"))
        self.setSubTitle(_("new_project_dialog.path.subtitle"))

        # Path input
        self.path_input = DirectoryEdit()

        self.registerField(
            "path*", self.path_input.input, "text", self.path_input.input.textChanged
        )

        # Error label
        self.error_label = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.path_input)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

    def validatePage(self):
        path = self.path_input.directory()
        if path is None or path == "" or not os.path.exists(path):
            self.error_label.setText(_("new_project_dialog.error.invalid_path"))
            return False

        self.error_label.setText("")
        return True

    def cleanupPage(self) -> None:
        self.error_label.setText("")
        self.path_input.setDirectory("")
        return super().cleanupPage()


class NamePage(QWizardPage):
    """
    Select a name for the new project. The name must be a valid folder name
    and the folder must not already exist in the selected path.
    """

    def __init__(self, *args, **kwargs):
        super(NamePage, self).__init__(*args, **kwargs)

        # Set the title and subtitle
        self.setTitle(_("new_project_dialog.name.title"))
        self.setSubTitle(_("new_project_dialog.name.subtitle"))

        # Name input
        self.name_input = QLineEdit()

        self.registerField(
            "name*", self.name_input, "text", self.name_input.textChanged
        )

        # Error label
        self.error_label = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.name_input)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

    def validatePage(self):
        name = self.name_input.text()
        if name is None or name == "" or not is_valid_folder_name(name):
            self.error_label.setText(_("new_project_dialog.error.invalid_folder_name"))
            return False

        path = self.field("path")
        full_path = Path(path) / name
        if os.path.exists(full_path):
            self.error_label.setText(
                _(
                    "new_project_dialog.error.folder_already_exists",
                    full_path.as_posix(),
                )
            )
            return False

        self.error_label.setText("")
        return True

    def cleanupPage(self) -> None:
        self.error_label.setText("")
        self.name_input.setText("")
        return super().cleanupPage()
