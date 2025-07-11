# ==========================================================================
# File: export_pdf.py
# Description: PyQT6 print to pdf dialog component.
# Date: 14/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------


from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF, QUrl
from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFileDialog,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.translator import translate as _
from proteus.application.state.manager import StateManager
from proteus.controller.command_stack import Controller
from proteus.application.export_strategy import ExportStrategy


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
FILE_EXTENSION_PDF: str = "pdf"


# --------------------------------------------------------------------------
# Class: ExportPDF
# Description: Class for the PROTEUS application export to PDF strategy.
# Date: 22/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ExportPDF(ExportStrategy):
    """
    Class for the PROTEUS application export to PDF strategy.

    It exports the current view to PDF format. It uses PyQt6
    QWebEnginePage.printToPdf() method to perform the export.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)

        self._export_widget: QWidget = None
        self._input: QLineEdit = None
        self._browse_button: QPushButton = None
        self._error_label: QLabel = None

    # ======================================================================
    # Implementation of the abstract methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : export
    # Description: Exports the current view to PDF format.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def export(self) -> None:
        """
        Exports the current view to PDF format.

        It uses PyQt6 QWebEnginePage.printToPdf() method to perform the export.
        It does not instantiate QWebChannel objects.

        Emits the exportFinishedSignal with the path to the exported file and
        a boolean indicating if the export was successful.
        """
        # NOTE: Page loading and pdf printing are asynchronous, so we need to
        # wait until the page is loaded to print the pdf and the variable page
        # must be a instance attribute to avoid garbage collection.
        # To solve this problem, helper functions are used to ensure that they
        # are executed in the correct order.
        self.page: QWebEnginePage = QWebEnginePage()

        def load_page() -> None:
            # Get current application state
            current_view = StateManager().get_current_view()

            # Generate html view
            html_view_path: str = self._controller.get_html_view_path(xslt_name=current_view)

            url: QUrl = QUrl.fromLocalFile(html_view_path)
            self.page.load(url)

            self.exportProgressSignal.emit(33)

        def print_page() -> None:
            self.exportProgressSignal.emit(65)
            # Define the margin values (in millimeters)
            margins: QMarginsF = QMarginsF(25, 25, 25, 25)

            # Create a QPageLayout object from the options dictionary
            page_layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                margins,
            )

            # Print to pdf the current view with margins
            file_path: str = self._input.text()
            self.page.printToPdf(file_path, page_layout)

        # Create the page and print it to pdf
        load_page()
        self.page.loadFinished.connect(print_page)
        # Show a dialog when the pdf printing is finished
        self.page.pdfPrintingFinished.connect(
            lambda: self.exportProgressSignal.emit(100)
        )
        self.page.pdfPrintingFinished.connect(
            lambda path, success: self.exportFinishedSignal.emit(path, success)
        )

    # ----------------------------------------------------------------------
    # Method     : exportFormWidget
    # Description: Creates the export form widget for the export pdf strategy.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def exportFormWidget(self) -> QWidget:
        """
        Creates the export form widget for the export pdf strategy.

        The pdf export widget is a simple line edit with a browse button.
        User may browse the file system and select the path/name of the
        exported file. The widget also provides a error message label.
        """

        self._export_widget = QWidget()

        # Widget creation --------------------------------------------------
        # Line edit
        self._input = QLineEdit()
        self._input.setDisabled(True)

        # Browse button
        browse_button_icon = Icons().icon(
            ProteusIconType.App, "browse_file_icon"
        )
        self._browse_button = QPushButton()
        self._browse_button.setIcon(browse_button_icon)

        # Information label
        info_label = QLabel()
        info_label.setText(_("export_dialog.export_pdf.filename.label"))

        # Error label
        self._error_label = QLabel()
        self._error_label.setObjectName("error_label")
        self._error_label.setWordWrap(True)
        self._error_label.setHidden(True)

        # Layout setup -----------------------------------------------------
        layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        input_layout.addWidget(self._input)
        input_layout.addWidget(self._browse_button)
        input_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(info_label)
        layout.addLayout(input_layout)
        layout.addWidget(self._error_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self._export_widget.setLayout(layout)

        # Connect signals --------------------------------------------------
        self._browse_button.clicked.connect(self._select_file_path)
        self._input.textChanged.connect(self._validate_file_path)

        return self._export_widget

    # ======================================================================
    # Private methods
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : _select_file_path
    # Description: Opens a file dialog to select the file path/name.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _select_file_path(self):
        """
        Opens a file dialog to select the file path/name.

        The file dialog is configured to select only pdf files and
        the default file name is the current view name. If the user
        selects a file name without extension, the extension is added
        automatically.
        """
        # Build default file name
        current_view = StateManager().get_current_view()
        default_file_name: str = f"{current_view}.{FILE_EXTENSION_PDF}"

        # Open the file dialog and set the default file name
        file_dialog: QFileDialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setDefaultSuffix(FILE_EXTENSION_PDF)
        file_dialog.setNameFilter(f"PDF files (*.{FILE_EXTENSION_PDF})")
        file_dialog.selectFile(default_file_name)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        # Get the selected file path and fix the extension if needed
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            path: str = file_dialog.selectedFiles()[0]
            if not path.endswith(f".{FILE_EXTENSION_PDF}"):
                path += f".{FILE_EXTENSION_PDF}"

            self._input.setText(path)

    # ----------------------------------------------------------------------
    # Method     : _validate_file_path
    # Description: Validates if the selected file path and name is valid.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _validate_file_path(self) -> None:
        """
        Validates if the selected file path and name is valid.

        If it is valid, emit the readyToExportSignal with True as
        argument. Otherwise, emit the readyToExportSignal with False
        as argument and set the error label text.
        """
        # Get file path and convert it to Path
        path_text: str = self._input.text()
        path: Path = Path(path_text)

        # Check if file name contains invalid characters
        invalid_chars: str = '<>:"/\\|?*'
        if any(char in invalid_chars for char in path.name):
            self._error_label.setText(
                _("export_dialog.export_pdf.filename.error.invalid_chars")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if file name is empty
        if path.name == "" or path.name == f".{FILE_EXTENSION_PDF}":
            self._error_label.setText(
                _("export_dialog.export_pdf.filename.error.empty")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # Check if the folder exists
        if not path.parent.exists():
            self._error_label.setText(
                _("export_dialog.export_pdf.filename.error.folder_not_found")
            )
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
            return

        # If everything is ok, hide the error label and emit the signal
        self._error_label.setHidden(True)
        self.readyToExportSignal.emit(True)
