# ==========================================================================
# File: export_latex.py
# Description: PROTEUS export strategies based on LaTeX templates:
#              - ExportLaTeX: LaTeX sources (main.tex and resources folder).
#              - ExportPDFLaTeX: PDF compiled from the LaTeX sources with
#                a LaTeX engine installed in the system.
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path
from typing import Dict, List
import logging
import re
import shutil
import tempfile

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QWidget, QLabel, QComboBox

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ASSETS_REPOSITORY
from proteus.model.template import Template, TEMPLATE_OUTPUT_LATEX
from proteus.application.configuration.config import Config
from proteus.application.state.manager import StateManager
from proteus.application.resources.translator import translate as _
from proteus.controller.command_stack import Controller

from basic.export.export_html import ExportHTML, remove_empty_directories
from basic.export.export_pdf import ExportPDF

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

LATEX_MAIN_FILE: str = "main.tex"
LATEX_ICONS_FOLDER: str = "icons"

# Supported engines in order of preference. latexmk is not used because
# MiKTeX on Windows does not ship the Perl interpreter it needs.
LATEX_ENGINES: List[str] = ["xelatex", "lualatex", "pdflatex"]

# Two passes are enough for the table of contents and cross-references
LATEX_PASSES: int = 2

# Image formats graphicx cannot include: converted to PNG on export
UNSUPPORTED_IMAGE_SUFFIXES = {".gif", ".bmp", ".webp", ".svg", ".tif", ".tiff", ".ico"}

# Assets are referenced as {assets/<file name>} by LaTeX templates
ASSET_REFERENCE_PATTERN = re.compile(r"\{" + ASSETS_REPOSITORY + r"/([^{}]+)\}")


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------


def get_latex_templates(controller: Controller) -> List[Template]:
    """
    Templates of the current profile that generate LaTeX.
    """
    return controller.get_templates_by_output_format(TEMPLATE_OUTPUT_LATEX)


def find_latex_engines() -> Dict[str, str]:
    """
    LaTeX engines found in the PATH, as a dictionary name -> executable.
    """
    engines: Dict[str, str] = {}
    for engine in LATEX_ENGINES:
        executable = shutil.which(engine)
        if executable:
            engines[engine] = executable
    return engines


def _copy_asset(asset: str, assets_folder: Path, destination: Path) -> str:
    """
    Copies an asset to the destination folder and returns the file name to
    be used in LaTeX. Images in formats LaTeX cannot include are converted
    to PNG.
    """
    source: Path = assets_folder / asset
    if not source.is_file():
        log.warning(f"Asset '{asset}' referenced in LaTeX not found in {assets_folder}")
        return asset

    destination.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() in UNSUPPORTED_IMAGE_SUFFIXES:
        converted = f"{asset}.png"
        image = QImage(source.as_posix())
        if not image.isNull() and image.save((destination / converted).as_posix(), "PNG"):
            return converted
        log.warning(f"Asset '{asset}' could not be converted to PNG")

    shutil.copy2(source, destination / asset)
    return asset


def write_latex_sources(controller: Controller, template: Template, folder: Path) -> Path:
    """
    Renders the current document with the given LaTeX template and writes
    the sources in the given folder:
    - main.tex
    - the template files except XSL and XML files (e.g. resources/proteus.sty)
    - the profile icons (icons/<class>.png)
    - the project assets referenced in main.tex (assets/...)

    :return: path to main.tex
    """
    tex: str = controller.render_template(template.name)

    # RenderService returns an <errors> HTML element if the XSLT failed
    if tex.lstrip().startswith("<errors>"):
        raise RuntimeError(f"Template '{template.name}' could not be rendered: {tex.strip()}")

    folder.mkdir(parents=True, exist_ok=True)

    # Template resources
    for item in template.path.iterdir():
        if item.is_file() and item.suffix not in [".xsl", ".xml"]:
            shutil.copy2(item, folder / item.name)
        elif item.is_dir():
            shutil.copytree(
                item,
                folder / item.name,
                ignore=shutil.ignore_patterns("*.xsl", "*.xml"),
                dirs_exist_ok=True,
            )
            # Folders that only contained XSLT modules
            remove_empty_directories(folder / item.name)

    # Profile icons
    icons_directory: Path = Config().profile_settings.icons_directory
    if icons_directory is not None and icons_directory.exists():
        (folder / LATEX_ICONS_FOLDER).mkdir(exist_ok=True)
        for icon in icons_directory.glob("*.png"):
            shutil.copy2(icon, folder / LATEX_ICONS_FOLDER / icon.name)

    # Referenced assets
    assets_folder: Path = StateManager().current_project_path / ASSETS_REPOSITORY
    copied: Dict[str, str] = {}
    for asset in set(ASSET_REFERENCE_PATTERN.findall(tex)):
        copied[asset] = _copy_asset(asset, assets_folder, folder / ASSETS_REPOSITORY)

    tex = ASSET_REFERENCE_PATTERN.sub(
        lambda match: "{%s/%s}" % (ASSETS_REPOSITORY, copied.get(match.group(1), match.group(1))),
        tex,
    )

    main_file: Path = folder / LATEX_MAIN_FILE
    main_file.write_text(tex, encoding="utf-8")
    return main_file


def _template_selector(controller: Controller) -> QComboBox:
    """
    Combo box with the LaTeX templates of the profile.
    """
    selector = QComboBox()
    for template in get_latex_templates(controller):
        selector.addItem(_(f"xslt_templates.{template.name}"), template)
    return selector


# --------------------------------------------------------------------------
# Class: ExportLaTeX
# Description: Export strategy that writes the LaTeX sources.
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
class ExportLaTeX(ExportHTML):
    """
    Exports the current document as LaTeX sources in a new folder, using a
    LaTeX template of the profile instead of the current view. The form is
    the HTML one (destination directory and folder name) plus a template
    selector.
    """

    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)
        self._template_selector: QComboBox = None

    def export(self) -> None:
        """
        Writes main.tex and its resources in the selected folder.
        """
        export_folder: Path = Path(self._path_input.directory()) / self._folder_name_input.text()
        template: Template = self._template_selector.currentData()

        try:
            self.exportProgressSignal.emit(20)
            export_folder.mkdir(parents=True)
            write_latex_sources(self._controller, template, export_folder)
        except Exception as e:
            log.error(f"Error exporting with LaTeX template '{template.name}': {e}")
            if export_folder.exists():
                shutil.rmtree(export_folder, ignore_errors=True)
            self.exportFinishedSignal.emit(export_folder.as_posix(), False)
            return

        self.exportProgressSignal.emit(100)
        self.exportFinishedSignal.emit(export_folder.as_posix(), True)

    def exportFormWidget(self) -> QWidget:
        """
        HTML export form plus a LaTeX template selector.
        """
        widget: QWidget = super().exportFormWidget()
        self._folder_name_input.setText(
            f"{StateManager().get_current_view()}-exported-latex"
        )

        self._template_selector = _template_selector(self._controller)
        layout = widget.layout()
        layout.insertWidget(0, QLabel(_("export_dialog.export_latex.template.label")))
        layout.insertWidget(1, self._template_selector)

        return widget

    def _validate_directory(self) -> None:
        super()._validate_directory()

        if self._template_selector is not None and self._template_selector.count() == 0:
            self._error_label.setText(_("export_dialog.export_latex.error.no_template"))
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)


# --------------------------------------------------------------------------
# Class: ExportPDFLaTeX
# Description: Export strategy that compiles the LaTeX sources to PDF.
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
class ExportPDFLaTeX(ExportPDF):
    """
    Exports the current document to PDF through LaTeX: the sources are
    written in a temporary folder and compiled with a LaTeX engine found in
    the PATH (xelatex, lualatex or pdflatex). The engine runs in a QProcess
    so that the application is not blocked. If the compilation fails, the
    LaTeX log is copied next to the selected PDF file.
    """

    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)
        self._template_selector: QComboBox = None
        self._engine_selector: QComboBox = None
        self._process: QProcess = None
        self._build_folder: Path = None
        self._pass: int = 0

    def export(self) -> None:
        """
        Writes the LaTeX sources in a temporary folder and starts the first
        compilation pass.
        """
        template: Template = self._template_selector.currentData()
        self._build_folder = Path(tempfile.mkdtemp(prefix="proteus-latex-"))

        try:
            write_latex_sources(self._controller, template, self._build_folder)
        except Exception as e:
            log.error(f"Error generating LaTeX with template '{template.name}': {e}")
            self._finish(False)
            return

        self.exportProgressSignal.emit(20)
        self._pass = 0
        self._run_engine()

    def _run_engine(self) -> None:
        """
        Runs one pass of the selected LaTeX engine.
        """
        self._pass += 1
        engine: str = self._engine_selector.currentData()

        self._process = QProcess()
        self._process.setWorkingDirectory(self._build_folder.as_posix())
        self._process.finished.connect(self._engine_finished)
        self._process.errorOccurred.connect(self._engine_error)
        self._process.start(
            engine, ["-interaction=nonstopmode", "-halt-on-error", LATEX_MAIN_FILE]
        )

    def _engine_error(self, error: QProcess.ProcessError) -> None:
        # Only errors that prevent the process from running are handled
        # here; a failed compilation is detected in _engine_finished.
        if error == QProcess.ProcessError.FailedToStart:
            log.error(f"LaTeX engine '{self._engine_selector.currentData()}' failed to start")
            self._finish(False)

    def _engine_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            log.error(f"LaTeX compilation failed (pass {self._pass}, exit code {exit_code})")
            self._finish(False)
            return

        self.exportProgressSignal.emit(20 + 70 * self._pass // LATEX_PASSES)

        if self._pass < LATEX_PASSES:
            self._run_engine()
        else:
            self._finish(True)

    def _finish(self, success: bool) -> None:
        """
        Copies the PDF (or the LaTeX log if the compilation failed) next to
        the selected file, removes the temporary folder and emits the
        finished signal.
        """
        file_path: Path = Path(self._input.text())

        try:
            if success:
                shutil.copy2(self._build_folder / "main.pdf", file_path)
            elif self._build_folder is not None and (self._build_folder / "main.log").exists():
                log_file = file_path.with_suffix(".log")
                shutil.copy2(self._build_folder / "main.log", log_file)
                log.error(f"LaTeX log copied to '{log_file}'")
        except Exception as e:
            log.error(f"Error copying the LaTeX output: {e}")
            success = False

        if self._build_folder is not None:
            shutil.rmtree(self._build_folder, ignore_errors=True)

        if success:
            self.exportProgressSignal.emit(100)
        self.exportFinishedSignal.emit(file_path.as_posix(), success)

    def exportFormWidget(self) -> QWidget:
        """
        PDF export form plus LaTeX template and engine selectors.
        """
        widget: QWidget = super().exportFormWidget()

        self._template_selector = _template_selector(self._controller)

        self._engine_selector = QComboBox()
        for engine, executable in find_latex_engines().items():
            self._engine_selector.addItem(engine, executable)

        layout = widget.layout()
        layout.insertWidget(0, QLabel(_("export_dialog.export_latex.template.label")))
        layout.insertWidget(1, self._template_selector)
        layout.insertWidget(2, QLabel(_("export_dialog.export_pdf_latex.engine.label")))
        layout.insertWidget(3, self._engine_selector)

        # Show missing prerequisites from the beginning
        error: str = self._missing_prerequisite()
        if error:
            self._error_label.setText(error)
            self._error_label.setHidden(False)

        return widget

    def _missing_prerequisite(self) -> str:
        """
        Error message if there is no LaTeX template or no LaTeX engine,
        empty string otherwise.
        """
        if self._template_selector is not None and self._template_selector.count() == 0:
            return _("export_dialog.export_latex.error.no_template")
        if self._engine_selector is not None and self._engine_selector.count() == 0:
            return _("export_dialog.export_pdf_latex.error.no_engine")
        return ""

    def _validate_file_path(self) -> None:
        super()._validate_file_path()

        error: str = self._missing_prerequisite()
        if error:
            self._error_label.setText(error)
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
