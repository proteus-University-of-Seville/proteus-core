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
from typing import Callable, Dict, List, Set
import hashlib
import logging
import re
import shutil
import tempfile
import threading
import urllib.request

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QObject, QProcess, QRunnable, QThreadPool, pyqtSignal
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
from basic.export.file_names import document_file_name
from basic.proteus_xslt_latex import latex_url

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

LATEX_MAIN_FILE: str = "main.tex"
LATEX_ICONS_FOLDER: str = "icons"

# Supported engines in order of preference (the first one found is the
# default in the export form): xelatex and lualatex support any Unicode
# character, pdflatex fails with characters it does not know (e.g. arrows
# or emojis), and xelatex is faster than lualatex. latexmk is not used
# because MiKTeX on Windows does not ship the Perl interpreter it needs.
LATEX_ENGINES: List[str] = ["xelatex", "lualatex", "pdflatex"]

# The engine is run until the auxiliary files do not change (the table of
# contents, cross-references and citations are stable), at least twice and
# at most LATEX_MAX_PASSES times, in case they never stabilize
LATEX_MIN_PASSES: int = 2
LATEX_MAX_PASSES: int = 4

# Auxiliary files written by each pass and read by the next one
LATEX_AUXILIARY_SUFFIXES: List[str] = [".aux", ".toc", ".out"]

# Warnings of LaTeX and its packages asking for another pass
LATEX_RERUN_PATTERN = re.compile(
    r"Rerun to get|Label\(s\) may have changed|Rerun LaTeX|[Pp]lease rerun"
)

# Image formats graphicx cannot include: converted to PNG on export
UNSUPPORTED_IMAGE_SUFFIXES = {".gif", ".bmp", ".webp", ".svg", ".tif", ".tiff", ".ico"}

# Assets are referenced as {assets/<file name>} by LaTeX templates
ASSET_REFERENCE_PATTERN = re.compile(r"\{" + ASSETS_REPOSITORY + r"/([^{}]+)\}")

# Remote figures are written as \ProteusRemoteImage{<width>}{<URL>} by LaTeX
# templates. They are downloaded to remote/ and replaced by \includegraphics.
REMOTE_IMAGE_PATTERN = re.compile(r"\\ProteusRemoteImage\{([^{}]*)\}\{([^{}]*)\}")
REMOTE_IMAGES_FOLDER: str = "remote"
REMOTE_IMAGE_TIMEOUT: int = 15  # seconds

# File signatures of the image formats graphicx can include as they are
INCLUDABLE_IMAGE_SIGNATURES = {
    b"\x89PNG": ".png",
    b"\xff\xd8": ".jpg",
    b"%PDF": ".pdf",
}


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


class LaTeXExportCancelled(Exception):
    """
    Raised while the LaTeX sources are being written if the export is
    cancelled.
    """


def latex_auxiliary_digest(folder: Path) -> str:
    """
    Digest of the auxiliary files of main.tex (aux, toc, out) in the given
    folder. If it does not change in a pass, another one is not needed.
    """
    digest = hashlib.sha256()
    for suffix in LATEX_AUXILIARY_SUFFIXES:
        auxiliary_file: Path = (folder / LATEX_MAIN_FILE).with_suffix(suffix)
        digest.update(suffix.encode())
        if auxiliary_file.is_file():
            digest.update(auxiliary_file.read_bytes())
    return digest.hexdigest()


def latex_rerun_needed(
    passes: int, previous_digest: str, digest: str, log_text: str
) -> bool:
    """
    True if the engine has to be run again after the given number of
    passes: always before LATEX_MIN_PASSES, never after LATEX_MAX_PASSES,
    and otherwise if the auxiliary files changed in the last pass or the
    log asks for another pass.
    """
    if passes < LATEX_MIN_PASSES:
        return True
    if passes >= LATEX_MAX_PASSES:
        return False
    return digest != previous_digest or LATEX_RERUN_PATTERN.search(log_text) is not None


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


def _download_image(url: str, destination: Path, name: str) -> str | None:
    """
    Downloads a remote image to the destination folder and returns its
    file name, or None if it could not be downloaded. PNG, JPEG and PDF
    files are kept as they are; any other format Qt can read (GIF, WebP,
    SVG...) is converted to PNG.
    """
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "PROTEUS"})
        with urllib.request.urlopen(request, timeout=REMOTE_IMAGE_TIMEOUT) as response:
            data: bytes = response.read()
    except Exception as e:
        log.warning(f"Remote figure '{url}' could not be downloaded: {e}")
        return None

    destination.mkdir(parents=True, exist_ok=True)

    for signature, suffix in INCLUDABLE_IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            (destination / f"{name}{suffix}").write_bytes(data)
            return f"{name}{suffix}"

    image = QImage.fromData(data)
    if not image.isNull() and image.save((destination / f"{name}.png").as_posix(), "PNG"):
        return f"{name}.png"

    log.warning(f"Remote figure '{url}' is not an image format that can be included")
    return None


def _not_cancelled() -> bool:
    return False


def _replace_remote_images(
    tex: str, folder: Path, cancelled: Callable[[], bool] = _not_cancelled
) -> str:
    """
    Downloads the remote figures of the LaTeX source to <folder>/remote and
    replaces each \\ProteusRemoteImage{width}{URL} by \\includegraphics, or
    by \\ProteusMissingImage{<link>} if the image could not be downloaded.
    Each URL is downloaded once.

    :raises LaTeXExportCancelled: if cancelled() is true before a download
    """
    downloaded: Dict[str, str | None] = {}

    def replace(match: re.Match) -> str:
        width, url = match.group(1), match.group(2).strip()
        if url not in downloaded:
            if cancelled():
                raise LaTeXExportCancelled()
            downloaded[url] = _download_image(
                url, folder / REMOTE_IMAGES_FOLDER, f"image-{len(downloaded) + 1}"
            )
        file_name = downloaded[url]
        if file_name is None:
            return r"\ProteusMissingImage{%s}" % latex_url(None, url)
        return r"\includegraphics[width=%s\linewidth]{%s/%s}" % (
            width, REMOTE_IMAGES_FOLDER, file_name
        )

    return REMOTE_IMAGE_PATTERN.sub(replace, tex)


def prepare_latex_sources(controller: Controller, template: Template, folder: Path) -> str:
    """
    First step of writing the LaTeX sources, run in the application thread
    because rendering uses the project and plugin components: renders the
    current document with the given LaTeX template and copies to the given
    folder:
    - the template files except XSL and XML files (e.g. resources/proteus.sty)
    - the profile icons (icons/<class>.png)
    - the project assets referenced in the LaTeX source (assets/...)

    :return: the LaTeX source, with remote figures still to be downloaded
             (see finish_latex_sources)
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

    return tex


def finish_latex_sources(
    tex: str, folder: Path, cancelled: Callable[[], bool] = _not_cancelled
) -> Path:
    """
    Second step of writing the LaTeX sources, which may take a while and
    can run in a worker thread (see LaTeXSourcesTask): downloads the remote
    figures (remote/...) and writes main.tex.

    :return: path to main.tex
    :raises LaTeXExportCancelled: if cancelled() is true before a download
    """
    tex = _replace_remote_images(tex, folder, cancelled)

    main_file: Path = folder / LATEX_MAIN_FILE
    main_file.write_text(tex, encoding="utf-8")
    return main_file


def write_latex_sources(controller: Controller, template: Template, folder: Path) -> Path:
    """
    Writes all the LaTeX sources in the given folder in the calling thread
    (prepare_latex_sources and finish_latex_sources).

    :return: path to main.tex
    """
    tex: str = prepare_latex_sources(controller, template, folder)
    return finish_latex_sources(tex, folder)


# --------------------------------------------------------------------------
# Class: LaTeXSourcesTask
# Description: Runs finish_latex_sources in a worker thread.
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
class LaTeXSourcesSignals(QObject):
    """
    Signals of LaTeXSourcesTask (QRunnable is not a QObject).
    - finished: path to main.tex and True, or an error message and False.
    """

    finished = pyqtSignal(str, bool)


class LaTeXSourcesTask(QRunnable):
    """
    Downloads the remote figures and writes main.tex (finish_latex_sources)
    in a thread of the global QThreadPool, so that the application does not
    stop responding while images are downloaded.

    Use start(): it keeps a reference to the running task until its finished
    signal has been delivered in the application thread. Receivers connected
    to the signal with a bound method of a QObject are disconnected
    automatically if they are deleted before the task finishes (e.g. when
    the export dialog is closed).

    The task can be cancelled with cancel(): it stops before the next
    download, removes the folder and does not emit its finished signal.
    """

    # Running tasks, so that they are not garbage collected
    _running: Set["LaTeXSourcesTask"] = set()

    def __init__(self, tex: str, folder: Path) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self._tex: str = tex
        self._folder: Path = folder
        self.signals = LaTeXSourcesSignals()

        # Shared with the worker thread, protected by _lock
        self._lock = threading.Lock()
        self._cancelled: bool = False
        self._done: bool = False

    def cancel(self) -> bool:
        """
        Cancels the task. Must be called from the application thread.

        :return: True if the task was still running: it removes the folder
                 itself and its finished signal is not emitted. False if it
                 had already finished: the caller must remove the folder,
                 since the finished signal may still be waiting to be
                 delivered to a receiver that is being deleted.
        """
        with self._lock:
            if self._done:
                return False
            self._cancelled = True
            return True

    def _is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def start(self) -> None:
        """
        Starts the task. Must be called from the application thread.
        """
        LaTeXSourcesTask._running.add(self)
        self.signals.finished.connect(
            lambda *args: LaTeXSourcesTask._running.discard(self)
        )
        QThreadPool.globalInstance().start(self)

    def run(self) -> None:
        result, success = "", False
        try:
            main_file: Path = finish_latex_sources(self._tex, self._folder, self._is_cancelled)
            result, success = main_file.as_posix(), True
        except LaTeXExportCancelled:
            pass
        except Exception as e:
            log.error(f"Error writing the LaTeX sources in '{self._folder}': {e}")
            result = str(e)

        with self._lock:
            self._done = True
            cancelled: bool = self._cancelled

        if cancelled:
            log.info(f"LaTeX export cancelled, '{self._folder}' removed")
            shutil.rmtree(self._folder, ignore_errors=True)
            LaTeXSourcesTask._running.discard(self)
            return

        self.signals.finished.emit(result, success)


def _cancel_sources_task(task: LaTeXSourcesTask, folder: Path) -> None:
    """
    Cancels the task that writes the LaTeX sources in the given folder. If
    it had already finished (or not started), the folder is removed here.
    """
    if task is None or not task.cancel():
        if folder is not None:
            shutil.rmtree(folder, ignore_errors=True)


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
        self._export_folder: Path = None
        self._task: LaTeXSourcesTask = None
        self._cancelled: bool = False

    def export(self) -> None:
        """
        Writes main.tex and its resources in the selected folder. Remote
        figures are downloaded in a worker thread; the export finishes in
        _sources_written.
        """
        self._cancelled = False
        self._export_folder = Path(self._path_input.directory()) / self._folder_name_input.text()
        template: Template = self._template_selector.currentData()

        try:
            self.exportProgressSignal.emit(10)
            self._export_folder.mkdir(parents=True)
            tex: str = prepare_latex_sources(self._controller, template, self._export_folder)
        except Exception as e:
            log.error(f"Error exporting with LaTeX template '{template.name}': {e}")
            self._sources_written(str(e), False)
            return

        self.exportProgressSignal.emit(40)
        self._task = LaTeXSourcesTask(tex, self._export_folder)
        self._task.signals.finished.connect(self._sources_written)
        self._task.start()

    def _sources_written(self, result: str, success: bool) -> None:
        """
        Emits the finished signal. If the sources could not be written, the
        export folder is removed.
        """
        if self._cancelled:
            return

        if not success:
            if self._export_folder.exists():
                shutil.rmtree(self._export_folder, ignore_errors=True)
            self.exportFinishedSignal.emit(self._export_folder.as_posix(), False)
            return

        self.exportProgressSignal.emit(100)
        self.exportFinishedSignal.emit(self._export_folder.as_posix(), True)

    def cancel(self) -> None:
        """
        Cancels the export: remote figures are no longer downloaded and the
        export folder is removed. The finished signal is not emitted.
        """
        self._cancelled = True
        _cancel_sources_task(self._task, self._export_folder)
        log.info(f"LaTeX export to '{self._export_folder}' cancelled")

    def exportFormWidget(self) -> QWidget:
        """
        HTML export form plus a LaTeX template selector.
        """
        widget: QWidget = super().exportFormWidget()
        self._folder_name_input.setText(
            f"{document_file_name(self._controller)}-exported-latex"
        )

        self._template_selector = _template_selector(self._controller)
        layout = widget.layout()
        layout.insertWidget(0, QLabel(_("export_dialog.export_latex.template.label")))
        layout.insertWidget(1, self._template_selector)

        return widget

    @classmethod
    def is_available(cls, controller: Controller) -> bool:
        """
        Only available if the profile has a LaTeX template.
        """
        return len(get_latex_templates(controller)) > 0


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
    so that the application is not blocked, until the auxiliary files are
    stable (see latex_rerun_needed). If the compilation fails, the LaTeX
    log is copied next to the selected PDF file.
    """

    # Default file name: <document acronym>_latex.pdf
    FILE_NAME_SUFFIX: str = "latex"

    def __init__(self, controller: Controller) -> None:
        super().__init__(controller)
        self._template_selector: QComboBox = None
        self._engine_selector: QComboBox = None
        self._process: QProcess = None
        self._task: LaTeXSourcesTask = None
        self._build_folder: Path = None
        self._pass: int = 0
        self._digest: str = ""
        self._cancelled: bool = False

    def export(self) -> None:
        """
        Writes the LaTeX sources in a temporary folder (remote figures are
        downloaded in a worker thread) and then starts the first compilation
        pass in _sources_written.
        """
        self._cancelled = False
        template: Template = self._template_selector.currentData()
        self._build_folder = Path(tempfile.mkdtemp(prefix="proteus-latex-"))

        try:
            self.exportProgressSignal.emit(5)
            tex: str = prepare_latex_sources(self._controller, template, self._build_folder)
        except Exception as e:
            log.error(f"Error generating LaTeX with template '{template.name}': {e}")
            self._finish(False)
            return

        self.exportProgressSignal.emit(10)
        self._task = LaTeXSourcesTask(tex, self._build_folder)
        self._task.signals.finished.connect(self._sources_written)
        self._task.start()

    def _sources_written(self, result: str, success: bool) -> None:
        """
        Starts the compilation once main.tex has been written.
        """
        if self._cancelled:
            return

        if not success:
            self._finish(False)
            return

        self.exportProgressSignal.emit(20)
        self._pass = 0
        self._digest = latex_auxiliary_digest(self._build_folder)
        self._run_engine()

    def _run_engine(self) -> None:
        """
        Runs one pass of the selected LaTeX engine.
        """
        self._pass += 1
        engine: str = self._engine_selector.currentData()

        # Child of the strategy, so that it is not left running if the
        # strategy is deleted
        self._process = QProcess(self)
        self._process.setWorkingDirectory(self._build_folder.as_posix())
        self._process.finished.connect(self._engine_finished)
        self._process.errorOccurred.connect(self._engine_error)
        self._process.start(
            engine, ["-interaction=nonstopmode", "-halt-on-error", LATEX_MAIN_FILE]
        )

    def _engine_error(self, error: QProcess.ProcessError) -> None:
        # Only errors that prevent the process from running are handled
        # here; a failed compilation is detected in _engine_finished.
        if self._cancelled:
            return
        if error == QProcess.ProcessError.FailedToStart:
            log.error(f"LaTeX engine '{self._engine_selector.currentData()}' failed to start")
            self._finish(False)

    def _engine_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if self._cancelled:
            return

        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            log.error(f"LaTeX compilation failed (pass {self._pass}, exit code {exit_code})")
            self._finish(False)
            return

        # Usually LATEX_MIN_PASSES are run: the progress bar is computed for
        # them and stays at 90% during any extra pass
        self.exportProgressSignal.emit(min(90, 20 + 70 * self._pass // LATEX_MIN_PASSES))

        previous_digest: str = self._digest
        self._digest = latex_auxiliary_digest(self._build_folder)
        log_file: Path = self._build_folder / "main.log"
        log_text: str = (
            log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
        )

        if latex_rerun_needed(self._pass, previous_digest, self._digest, log_text):
            self._run_engine()
            return

        if self._pass >= LATEX_MAX_PASSES and self._digest != previous_digest:
            log.warning(
                f"LaTeX auxiliary files still changing after {self._pass} passes; "
                "cross-references may be wrong"
            )
        log.info(f"LaTeX compilation finished after {self._pass} passes")
        self._finish(True)

    def cancel(self) -> None:
        """
        Cancels the export: the LaTeX engine is stopped (or the remote
        figures are no longer downloaded) and the temporary folder is
        removed. The finished signal is not emitted.
        """
        self._cancelled = True

        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            # The folder cannot be removed on Windows while the engine is running
            self._process.waitForFinished(5000)

        _cancel_sources_task(self._task, self._build_folder)
        log.info("PDF export from LaTeX cancelled")

    def _finish(self, success: bool) -> None:
        """
        Copies the PDF (or the LaTeX log if the compilation failed) next to
        the selected file, removes the temporary folder and emits the
        finished signal.
        """
        if self._cancelled:
            return

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

        # Show the missing engine from the beginning
        error: str = self._missing_engine()
        if error:
            self._error_label.setText(error)
            self._error_label.setHidden(False)

        return widget

    @classmethod
    def is_available(cls, controller: Controller) -> bool:
        """
        Only available if the profile has a LaTeX template. A missing LaTeX
        engine is shown as an error in the form instead, so that the user
        knows that it can be installed.
        """
        return len(get_latex_templates(controller)) > 0

    def _missing_engine(self) -> str:
        """
        Error message if there is no LaTeX engine, empty string otherwise.
        """
        if self._engine_selector is not None and self._engine_selector.count() == 0:
            return _("export_dialog.export_pdf_latex.error.no_engine")
        return ""

    def _validate_file_path(self) -> None:
        super()._validate_file_path()

        error: str = self._missing_engine()
        if error:
            self._error_label.setText(error)
            self._error_label.setHidden(False)
            self.readyToExportSignal.emit(False)
