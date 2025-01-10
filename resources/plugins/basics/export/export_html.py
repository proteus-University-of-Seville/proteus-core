# ==========================================================================
# File: export_html.py
# Description: PyQT6 print to pdf dialog component.
# Date: 14/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path
import shutil
import logging
import re

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QLabel,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ASSETS_REPOSITORY
from proteus.application import ASSETS_DUMMY_SEARCH_PATH, TEMPLATE_DUMMY_SEARCH_PATH
from proteus.application.state.manager import StateManager
from proteus.application.resources.translator import translate as _
from proteus.controller.command_stack import Controller
from proteus.application.export_strategy import ExportStrategy
from proteus.views.forms.directory_edit import DirectoryEdit
from proteus.views.forms import validators

# Module configuration
log = logging.getLogger(__name__) # Logger


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
FILE_EXTENSION_HTML: str = "html"


# --------------------------------------------------------------------------
# Class: ExportHTML
# Description: Class for the PROTEUS application export to HTML strategy.
# Date: 22/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ExportHTML(ExportStrategy):
    """
    Class for the PROTEUS application export to HTML strategy.

    It export the current view HTML to a folder with all its local resources.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Object initialization.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)

        self._controller = controller

        self._export_widget: QWidget = None
        self._path_input: DirectoryEdit = None
        self._folder_name_input: QLineEdit = None
        self._error_label: QLabel = None

    # ======================================================================
    # Implementation of the abstract methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : export
    # Description: Exports the current view to HTML.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def export(self) -> None:
        """
        Exports the current view to HTML. It creates a folder with the HTML
        file and all its local resources (assets and XSLT resources).

        The algorithm takes the following steps:
        - Create the export folder.
        - Copy the project assets folder to the export folder (if it exists).
        - Copy the XSLT current template folder to the export folder. Exclude
          from the copy all the XSL files.
        - Replace all the 'assets:///' dummy URLs from 'src' attributes with
          the string './assets/'.
        - Replace all the 'templates:///<current_tempalte_name>' dummy URLs
          from 'src' attributes with the string './resources/'.
        - Write the processed HTML to the export folder.

        If any error occurs, the export is aborted and the exportFinishedSignal
        is emitted with the failed export folder path and False as arguments.
        Otherwise, the exportFinishedSignal is emitted with the successful
        export folder path and True as arguments.
        """
        # Current view and HTML
        current_view: str = StateManager().get_current_view()
        html: str = self._controller.get_html_view(current_view)
        folder_name: str = self._folder_name_input.text()

        try:

            # ------------------------------------------------------------------
            # Create the export folder
            export_folder: Path = Path(self._path_input.directory()) / folder_name
            export_folder.mkdir(parents=True)

            self.exportProgressSignal.emit(15)

            # ------------------------------------------------------------------
            # Copy the project assets folder to the export folder
            assets_folder: Path = StateManager().current_project_path / ASSETS_REPOSITORY
            assets_folder_destination: Path = export_folder / ASSETS_REPOSITORY

            if assets_folder.exists():
                shutil.copytree(assets_folder, assets_folder_destination)

            self.exportProgressSignal.emit(40)

            # ------------------------------------------------------------------
            # Copy the current XSLT template folder excluding XSL and XML files
            template = self._controller.get_template_by_name(current_view)

            for file_dir in template.path.iterdir():
                if file_dir.is_file() and file_dir.suffix not in [".xsl", ".xml"]:
                    shutil.copy2(
                        file_dir,
                        export_folder / file_dir.name
                    )
                elif file_dir.is_dir():
                    shutil.copytree(
                        file_dir,
                        export_folder / file_dir.name,
                        ignore=shutil.ignore_patterns("*.xsl", "*.xml"),
                    )

            self.exportProgressSignal.emit(50)

            # ------------------------------------------------------------------
            # Remove the empty directories and assets that are not used in the HTML

            # Remove unused assets, if assets folder exists
            if assets_folder_destination.exists():
                assests_pattern = re.compile(r"(?<=\")(assets:///.*?[^\"\.])(?=\")")
                assets_matches = assests_pattern.findall(html)
                necessary_assets = [asset.split("/")[-1] for asset in assets_matches]
                for asset in assets_folder_destination.iterdir():
                    if asset.is_file() and asset.name not in necessary_assets:
                        asset.unlink()

            # Remove empty directories
            remove_empty_directories(export_folder)

            self.exportProgressSignal.emit(65)

            # ------------------------------------------------------------------
            # Replace all the 'assets:///' dummy URLs from 'src' attributes with
            # the string './assets/'
            html = html.replace(f"{ASSETS_DUMMY_SEARCH_PATH}:///", "./assets/")

            self.exportProgressSignal.emit(75)

            # ------------------------------------------------------------------
            # Replace all the 'templates:///<current_tempalte_name>' dummy URLs
            # from 'src' attributes with the string './resources/'
            html = html.replace(
                f"{TEMPLATE_DUMMY_SEARCH_PATH}:///{current_view}/",
                "./",
            )

            self.exportProgressSignal.emit(85)

            # ------------------------------------------------------------------
            # Write the processed HTML to the export folder
            html_file: Path = export_folder / f"index.{FILE_EXTENSION_HTML}"
            html_file.write_text(html, encoding="utf-8")
        except Exception as e:
            # Emit the exportFinishedSignal
            log.error(f"Error exporting view '{current_view}' to HTML: {e}")
            self.exportFinishedSignal.emit(export_folder.as_posix(), False)

            # If the export folder exists, delete it
            if export_folder.exists():
                shutil.rmtree(export_folder)

            return

        # Emit the exportFinishedSignal
        self.exportProgressSignal.emit(100)
        self.exportFinishedSignal.emit(export_folder.as_posix(), True)


    # ----------------------------------------------------------------------
    # Method     : exportFormWidget
    # Description: Creates the export form widget for the export html strategy.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def exportFormWidget(self) -> QWidget:
        """
        Creates the export form widget for the export html strategy.

        The html export widget is line edit with a browse button to select
        the export directory and a line edit to set the folder name. It also
        has an error label to show the error messages for both inputs.

        The default folder name is <current_view>-exported-html.
        """

        self._export_widget = QWidget()

        # Widget creation --------------------------------------------------
        # Line edit
        self._path_input = DirectoryEdit()
        self._folder_name_input = QLineEdit()

        # Set default folder name
        self._folder_name_input.setText(
            f"{StateManager().get_current_view()}-exported-html"
        )

        # Information labels
        path_info_label = QLabel()
        path_info_label.setText(
            _("export_dialog.export_html.filepath.label")
        )

        folder_name_info_label = QLabel()
        folder_name_info_label.setText(
            _("export_dialog.export_html.folder_name.label")
        )

        # Error label
        self._error_label = QLabel()
        self._error_label.setObjectName("error_label")
        self._error_label.setWordWrap(True)
        self._error_label.setHidden(True)

        # Layout setup -----------------------------------------------------
        layout = QVBoxLayout()
        layout.addWidget(folder_name_info_label)
        layout.addWidget(self._folder_name_input)
        layout.addWidget(path_info_label)
        layout.addWidget(self._path_input)
        layout.addWidget(self._error_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self._export_widget.setLayout(layout)

        # Connect signals --------------------------------------------------
        self._path_input.input.textChanged.connect(self._validate_directory)
        self._folder_name_input.textChanged.connect(self._validate_directory)

        return self._export_widget

    # ======================================================================
    # Private methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : _validate_directory
    # Description: Validates if the selected directory is valid.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _validate_directory(self) -> None:
        """
        Validates if the selected directory is valid.

        If it is valid, emit the readyToExportSignal with True as
        argument. Otherwise, emit the readyToExportSignal with False
        as argument and set the error label text.
        """
        # Get file path and convert it to Path
        path_text: str = self._path_input.directory()
        path: Path = Path(path_text)
        folder_name: str = self._folder_name_input.text()

        # Check if the path is empty
        if path_text == "":
            self._error_label.setText(
                _("export_dialog.export_html.error.empty")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if the path exists
        if not path.exists():
            self._error_label.setText(
                _("export_dialog.export_html.error.not_found")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return
        
        # Check if the path is a directory
        if not path.is_dir():
            self._error_label.setText(
                _("export_dialog.export_html.error.not_directory")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return
        
        # Check if folder name is valid
        if not validators.is_valid_folder_name(folder_name) or folder_name == "":
            self._error_label.setText(
                _("export_dialog.export_html.error.invalid_folder_name")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if the folder already exists
        if (path / folder_name).exists():
            self._error_label.setText(
                _("export_dialog.export_html.error.folder_exists")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # If everything is ok, hide the error label and emit the signal
        self._error_label.setHidden(True)
        self.readyToExportSignal.emit(True)



def remove_empty_directories(path: Path) -> None:
    """
    Removes all the empty directories from the given path.

    If the given path is an empty directory, it is removed. Otherwise, it
    recursively calls itself for each subdirectory.
    """
    if not path.is_dir():
        return

    for sub_path in path.iterdir():
        remove_empty_directories(sub_path)

    if not list(path.iterdir()):
        path.rmdir()