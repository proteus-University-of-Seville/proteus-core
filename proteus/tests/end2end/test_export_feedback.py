"""
Tests of what the export dialog tells the user while it is exporting: the
progress bar (including the busy mode), the elapsed time and the text panel
filled by the export strategies.
"""

import os
import shutil
import sys

import pytest
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from proteus.application.export_strategy import ExportStrategy
from proteus.application.resources.plugins import Plugins
from proteus.application.resources.translator import translate as _
from proteus.application.state.manager import StateManager
from proteus.tests.end2end.fixtures import app, load_project
from proteus.tests.end2end.test_export_latex import TEST_DOCUMENT_ID, TEST_PROJECT_NAME
from proteus.views.components.dialogs.base_dialogs import MessageBox
from proteus.views.components.dialogs.export_dialog import ExportDialog


def create_dialog(app, strategy_name: str) -> ExportDialog:
    """
    Loads the example project and creates the export dialog with the given
    export format selected.
    """
    load_project(main_window=app, project_name=TEST_PROJECT_NAME)
    app._controller._render_service.add_functions_to_namespace(Plugins().get_xslt_functions())
    StateManager().set_current_document(TEST_DOCUMENT_ID)
    StateManager().set_current_view("default")

    dialog = ExportDialog(controller=app._controller)
    selector = dialog.export_format_selector
    selector.setCurrentIndex(selector.findData(Plugins().get_export_strategies()[strategy_name]))
    return dialog


def test_panel_label_has_no_escaped_quotes():
    """
    The label of the panel is a plain text (it had escaped quotes).
    """
    label = _("export_dialog.log.label")

    assert label and '"' not in label and "\\" not in label


def test_report_tells_the_message_and_the_progress(app):
    """
    ExportStrategy.report adds a line to the text panel and updates the
    progress bar; both are optional.
    """
    load_project(main_window=app, project_name=TEST_PROJECT_NAME)
    strategy = Plugins().get_export_strategies()["pdf"](app._controller)
    logs, progresses = [], []
    strategy.exportLogSignal.connect(logs.append)
    strategy.exportProgressSignal.connect(progresses.append)

    strategy.report("one", 10)
    strategy.report("two\n")
    strategy.report(progress=ExportStrategy.PROGRESS_BUSY)
    strategy.report()

    assert logs == ["one\n", "two\n"]
    assert progresses == [10, ExportStrategy.PROGRESS_BUSY]


def test_progress_bar_busy_mode(app):
    """
    The progress bar shows that the export is working, without a percentage,
    until the next progress.
    """
    dialog = create_dialog(app, "pdf")
    strategy = dialog._export_strategy

    strategy.exportProgressSignal.emit(ExportStrategy.PROGRESS_BUSY)
    busy = (dialog.progress_bar.minimum(), dialog.progress_bar.maximum())
    strategy.exportProgressSignal.emit(50)

    assert busy == (0, 0)
    assert (dialog.progress_bar.minimum(), dialog.progress_bar.maximum()) == (0, 100)
    assert dialog.progress_bar.value() == 50
    dialog.deleteLater()


def test_elapsed_time_is_shown_only_while_exporting(app, monkeypatch):
    """
    The elapsed time starts with the export and stops when it finishes.
    """
    monkeypatch.setattr(MessageBox, "critical", staticmethod(lambda *args, **kwargs: None))
    dialog = create_dialog(app, "pdf")
    dialog._export_strategy.export = lambda: None
    dialog.show()
    inactive_at_first = not dialog._elapsed_timer.isActive() and dialog.elapsed_label.isHidden()

    dialog.export_button_clicked()
    running = dialog._elapsed_timer.isActive() and not dialog.elapsed_label.isHidden()
    text = dialog.elapsed_label.text()
    dialog._export_strategy.exportFinishedSignal.emit("file.pdf", False)

    assert inactive_at_first
    assert running and text.endswith("0:00")
    assert not dialog._elapsed_timer.isActive()
    dialog.deleteLater()


def export_to_pdf(app, qtbot, tmp_path, monkeypatch, strategy_name: str):
    """
    Exports the example document with the given strategy and returns what
    the strategy told the user and whether the export was successful.
    """
    monkeypatch.setattr(MessageBox, "critical", staticmethod(lambda *args, **kwargs: None))
    monkeypatch.setattr(MessageBox, "information", staticmethod(lambda *args, **kwargs: None))
    dialog = create_dialog(app, strategy_name)
    dialog.show()
    strategy = dialog._export_strategy
    output = tmp_path / "output.pdf"
    strategy._input.setText(str(output))

    progresses, results = [], []
    strategy.exportProgressSignal.connect(progresses.append)
    strategy.exportFinishedSignal.connect(lambda path, success: results.append(success))

    dialog.export_button_clicked()
    qtbot.waitUntil(lambda: bool(results), timeout=240000)

    panel_shown = not dialog.log_view.isHidden()
    text = dialog.log_view.toPlainText()
    dialog.deleteLater()
    return progresses, text, results[0], panel_shown, output


class FakeWebEnginePage(QObject):
    """
    Replaces QWebEnginePage in the tests of the export to PDF from HTML: it
    loads and "prints" at once, writing a small file. The real one needs a
    Chromium that does not run in every environment (it crashes the whole
    process with the virtual display of the continuous integration).
    """

    loadProgress = pyqtSignal(int)
    loadFinished = pyqtSignal(bool)
    pdfPrintingFinished = pyqtSignal(str, bool)

    def load(self, url) -> None:
        QTimer.singleShot(0, self._loaded)

    def _loaded(self) -> None:
        self.loadProgress.emit(30)
        self.loadProgress.emit(100)
        self.loadFinished.emit(True)

    def printToPdf(self, file_path, page_layout) -> None:
        with open(file_path, "wb") as pdf:
            pdf.write(b"%PDF-1.4\n" + b"0" * 4096)
        QTimer.singleShot(0, lambda: self.pdfPrintingFinished.emit(file_path, True))


def check_pdf_from_html_feedback(progresses, text, success, panel_shown, output):
    """
    What the export to PDF from HTML tells the user: the panel with its
    stages, the progress of the loading of the page, a busy bar while the PDF
    is generated and the final summary.
    """
    stages = [
        _("export_dialog.progress.pdf.generating_html"),
        _("export_dialog.progress.pdf.loading_page"),
        _("export_dialog.progress.pdf.printing"),
    ]
    positions = [text.find(stage) for stage in stages]
    assert success and output.exists()
    assert panel_shown
    assert -1 not in positions and positions == sorted(positions), text
    assert progresses[0] == 5
    assert ExportStrategy.PROGRESS_BUSY in progresses
    assert progresses[-1] == 100
    assert all(10 <= p <= 50 for p in progresses[1 : progresses.index(ExportStrategy.PROGRESS_BUSY)])
    assert " KB" in text.splitlines()[-1]


def test_pdf_from_html_tells_its_stages(app, qtbot, tmp_path, monkeypatch):
    """
    The export to PDF from HTML tells its stages (with a simulated page).
    """
    strategy_class = Plugins().get_export_strategies()["pdf"]
    monkeypatch.setattr(sys.modules[strategy_class.__module__], "QWebEnginePage", FakeWebEnginePage)

    check_pdf_from_html_feedback(*export_to_pdf(app, qtbot, tmp_path, monkeypatch, "pdf"))


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="QtWebEngine crashes the process printing to PDF with the virtual display of the CI",
)
def test_pdf_from_html_tells_its_stages_with_the_real_engine(app, qtbot, tmp_path, monkeypatch):
    """
    The same with the real QWebEnginePage, which prints the PDF.
    """
    check_pdf_from_html_feedback(*export_to_pdf(app, qtbot, tmp_path, monkeypatch, "pdf"))


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex is not installed")
def test_pdf_from_latex_progress_follows_the_pages(app, qtbot, tmp_path, monkeypatch):
    """
    In the first pass the total number of pages is not known: the bar is
    busy. In the second one, it follows the pages written.
    """
    progresses, text, success, panel_shown, output = export_to_pdf(
        app, qtbot, tmp_path, monkeypatch, "pdf_latex"
    )

    busy = ExportStrategy.PROGRESS_BUSY
    first_busy = progresses.index(busy)
    after_first_pass = progresses[first_busy + 1 :]
    assert success and output.exists()
    assert panel_shown
    assert _("export_dialog.progress.latex.pass", "xelatex", 1) in text
    assert _("export_dialog.progress.latex.pass", "xelatex", 2) in text
    # After the first pass (55) the bar follows the pages up to 90 without going back
    determinate = [p for p in after_first_pass if p != busy]
    assert determinate[0] == 55
    assert determinate == sorted(determinate)
    assert any(55 < p < 90 for p in determinate), determinate
    assert determinate[-1] == 100


def test_export_starts_after_the_dialog_is_painted(app, qtbot):
    """
    The export strategy is called once the event loop has run (so the dialog,
    which grows to show the progress bar, is painted before an export that
    does all its work at once), not from the click itself; and it is not
    called if the dialog is closed in between.
    """
    dialog = create_dialog(app, "html")
    calls = []
    dialog._export_strategy.export = lambda: calls.append(True)
    dialog._export_strategy.cancel = lambda: None

    dialog.export_button_clicked()
    called_by_the_click = bool(calls)
    qtbot.waitUntil(lambda: bool(calls), timeout=2000)

    # Closed before the event loop runs: nothing is exported
    calls.clear()
    dialog.export_button_clicked()
    dialog.reject()
    qtbot.wait(100)

    assert not called_by_the_click
    assert calls == []
    dialog.deleteLater()


def test_export_starts_after_the_pending_events_are_processed(app, monkeypatch):
    """
    The pending events of the dialog (layout and painting of the area that
    appears with the progress bar) are processed before the strategy starts
    working, which in the export to HTML does not return to the event loop.
    """
    from proteus.views.components.dialogs import export_dialog

    order = []

    class FakeApplication:
        @staticmethod
        def processEvents(flags=None):
            order.append("events")

    monkeypatch.setattr(export_dialog, "QApplication", FakeApplication)
    dialog = create_dialog(app, "html")
    dialog._export_strategy.export = lambda: order.append("export")

    dialog.export_button_clicked()
    dialog._start_export()

    assert order == ["events", "export"]
    dialog._exporting = False
    dialog.deleteLater()


@pytest.mark.parametrize("strategy_name", ["html", "latex", "pdf", "pdf_latex"])
def test_export_forms_show_no_error_when_they_are_created(app, strategy_name):
    """
    No format shows an error before the user does anything (the LaTeX form
    changed the default folder name after connecting the validation, which
    showed one).
    """
    dialog = create_dialog(app, strategy_name)
    strategy = dialog._export_strategy

    assert strategy._error_label.isHidden()
    if strategy_name in ("html", "latex"):
        suffix = "exported-html" if strategy_name == "html" else "exported-latex"
        assert strategy._folder_name_input.text().endswith("-" + suffix)
    dialog.deleteLater()
