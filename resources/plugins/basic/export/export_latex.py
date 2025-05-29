# ==========================================================================
# File: export_latex.py
# Description: PyQT6 print latex to pdf dialog component.
# Date: 20/01/2025
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path
import shutil
import logging
import subprocess
import re

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QDialog,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_TEMP_DIR
from proteus.model import ASSETS_REPOSITORY
from proteus.application import ASSETS_DUMMY_SEARCH_PATH, TEMPLATE_DUMMY_SEARCH_PATH
from proteus.application.resources.translator import translate as _
from proteus.application.state.manager import StateManager
from proteus.controller.command_stack import Controller
from proteus.application.export_strategy import ExportStrategy
from proteus.views.forms.directory_edit import DirectoryEdit
from proteus.views.forms.boolean_edit import BooleanEdit
from proteus.views.forms import validators

# Module configuration
log = logging.getLogger(__name__) # Logger

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
FILE_EXTENSION_LATEX: str = "tex"
FILE_EXTENSION_PDF: str = "pdf"
LATEX_HTML_TAG: str = "latex"  # Defined by convention in the XSLT
LATEX_TEMP_DIR: Path = PROTEUS_TEMP_DIR / "latex"


# --------------------------------------------------------------------------
# Class: ExportLaTeX
# Description: Class for the PROTEUS application export to pdflatex strategy.
# Date: 20/01/2025
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ExportLaTeX(ExportStrategy):
    """
    Class for the PROTEUS application export to pdflatex strategy.

    It uses local installed LaTeX features to invoke pdflatex command
    and generate a PDF file from the LaTeX code.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Date       : 20/01/2025
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)

        self._export_widget: QWidget = None
        self._path_input: DirectoryEdit = None
        self._folder_name_input: QLineEdit = None
        self._pdf_generation_input: BooleanEdit = None
        self._error_label: QLabel = None

    # ----------------------------------------------------------------------
    # Method     : export
    # Date       : 20/01/2025
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def export(self):
        # Current view and HTML
        current_view: str = StateManager().get_current_view()
        html: str = self._controller.get_html_view(current_view)
        folder_name: str = self._folder_name_input.text()

        # -----------------------------
        # FIRST PART: Export to LaTeX
        # -----------------------------

        try:
            # ------------------------------------------------------------------
            # Create the export folder
            export_folder: Path = Path(self._path_input.directory()) / folder_name
            export_folder.mkdir(parents=True)

            # Create the main LaTeX file where the LaTeX code will be written
            latex_file_path: Path = export_folder / f"main.{FILE_EXTENSION_LATEX}"
            latex_file_path.touch()

            self.exportProgressSignal.emit(5)

            # ------------------------------------------------------------------
            # Extract LaTeX code from the html view
            latex_code: str = (
                re.search(r"<latex>(.*?)<\/latex>", html, re.DOTALL).group(1).strip()
            )

            self.exportProgressSignal.emit(15)

            # ------------------------------------------------------------------
            # Copy the project assets folder to the export folder
            assets_folder: Path = StateManager().current_project_path / ASSETS_REPOSITORY
            assets_folder_destination: Path = export_folder / ASSETS_REPOSITORY

            if assets_folder.exists():
                shutil.copytree(assets_folder, assets_folder_destination)

            self.exportProgressSignal.emit(30)

            # ------------------------------------------------------------------
            # Copy the current XSLT template folder excluding XSL, XML and JS files
            template = self._controller.get_template_by_name(current_view)

            for file_dir in template.path.iterdir():
                if file_dir.is_file() and file_dir.suffix not in [".xsl", ".xml", ".js"]:
                    shutil.copy2(
                        file_dir,
                        export_folder / file_dir.name
                    )
                elif file_dir.is_dir():
                    shutil.copytree(
                        file_dir,
                        export_folder / file_dir.name,
                        ignore=shutil.ignore_patterns("*.xsl", "*.xml", "*.js"),
                    )

            self.exportProgressSignal.emit(40)

            # ------------------------------------------------------------------
            # Remove the empty directories and assets that are not used in the LaTeX code

            # Remove unused assets, if assets folder exists
            if assets_folder_destination.exists():
                assests_pattern = re.compile(r"(?<=\{)(assets:///.*?[^\.])(?=\})")
                assets_matches = assests_pattern.findall(latex_code)
                necessary_assets = [asset.split("/")[-1] for asset in assets_matches]
                for asset in assets_folder_destination.iterdir():
                    if asset.is_file() and asset.name not in necessary_assets:
                        asset.unlink()

            # Remove empty directories
            remove_empty_directories(export_folder)

            # ------------------------------------------------------------------
            # Replace all the 'assets:///' dummy URLs from 'src' attributes with
            # the string './assets/'
            latex_code = latex_code.replace(f"{ASSETS_DUMMY_SEARCH_PATH}:///", "./assets/")

            # Replace all the 'templates:///<current_tempalte_name>' dummy URLs
            # from 'src' attributes with the string './resources/'
            latex_code = latex_code.replace(
                f"{TEMPLATE_DUMMY_SEARCH_PATH}:///{current_view}/",
                "./",
            )

            self.exportProgressSignal.emit(60)

            # ------------------------------------------------------------------
            # Write the LaTeX file to the export folder
            latex_file_path.write_text(latex_code, encoding="utf-8")
        except Exception as e:
            # Emit the exportFinishedSignal
            log.error(f"Error exporting view '{current_view}' to LaTeX: {e}")
            self.exportFinishedSignal.emit(export_folder.as_posix(), False)

            # If the export folder exists, delete it
            if export_folder.exists():
                shutil.rmtree(export_folder)

            return
        

        # -----------------------------
        # SECOND PART: Export to PDF (non-critical)
        # -----------------------------
        if self._pdf_generation_input.checked():

            compile_dir = export_folder / "compile"

            try:
                # Calling pdflatex command twice to make sure references are resolved
                pdflatex(compile_dir, latex_file_path)
                pdflatex(compile_dir, latex_file_path)
            except subprocess.CalledProcessError as e:
                log_content = e.stdout.decode("utf-8") + e.stderr.decode("utf-8")
                # Create a new window with the log content
                log_window = QDialog()
                log_window.setWindowTitle(_("export_dialog.export_latex.error.log.title"))
                log_window.setModal(True)
                log_window.resize(800, 600)

                info_text = QLabel()
                info_text.setText(_("export_dialog.export_latex.error.log.info"))

                log_text = QTextEdit()
                log_text.setPlainText(log_content)
                log_text.setReadOnly(True)

                layout = QVBoxLayout()
                layout.addWidget(info_text)
                layout.addWidget(log_text)
                log_window.setLayout(layout)
                log_window.exec()

        # Emit the exportFinishedSignal
        self.exportProgressSignal.emit(100)
        self.exportFinishedSignal.emit(export_folder.as_posix(), True)

    # ----------------------------------------------------------------------
    # Method     : exportFormWidget
    # Date       : 20/01/2025
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def exportFormWidget(self):
        """
        Creates the export form widget for the export latex strategy.

        The latex export widget is a simple line edit with a browse button.
        User may browse the file system and select the path/name of the
        exported file. The widget also provides a error message label.
        """
        self._export_widget = QWidget()

        # Widget creation --------------------------------------------------
        # Line edit
        self._path_input = DirectoryEdit()
        self._folder_name_input = QLineEdit()

        # Set default folder name
        self._folder_name_input.setText(
            f"{StateManager().get_current_view()}-exported-latex"
        )

        # Boolean edit for PDF generation
        self._pdf_generation_input = BooleanEdit(_("export_dialog.export_latex.generate_pdf.label"))

        # Information labels
        path_info_label = QLabel()
        path_info_label.setText(
            _("export_dialog.export_latex.filepath.label")
        )

        folder_name_info_label = QLabel()
        folder_name_info_label.setText(
            _("export_dialog.export_latex.folder_name.label")
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
        layout.addWidget(self._pdf_generation_input)
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
                _("export_dialog.export_latex.error.empty")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if the path exists
        if not path.exists():
            self._error_label.setText(
                _("export_dialog.export_latex.error.not_found")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return
        
        # Check if the path is a directory
        if not path.is_dir():
            self._error_label.setText(
                _("export_dialog.export_latex.error.not_directory")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return
        
        # Check if folder name is valid
        if not validators.is_valid_folder_name(folder_name) or folder_name == "":
            self._error_label.setText(
                _("export_dialog.export_latex.error.invalid_folder_name")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if the folder already exists
        if (path / folder_name).exists():
            self._error_label.setText(
                _("export_dialog.export_latex.error.folder_exists")
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


def pdflatex(outputdir: Path, texfile: Path):
    subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={outputdir.as_posix()}",
            texfile.as_posix(),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        cwd=outputdir.parent.as_posix(),
    )