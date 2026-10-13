# ==========================================================================
# File: export_dialog.py
# Description: PyQT6 print to pdf dialog component.
# Date: 14/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import time
from typing import Callable

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QEventLoop, QSize, QTimer
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
    QProgressBar,
    QPlainTextEdit,
)


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.controller.command_stack import Controller
from proteus.application.resources.translator import translate as _
from proteus.application.export_strategy import ExportStrategy
from proteus.application.resources.plugins import Plugins
from proteus.views.components.dialogs.base_dialogs import ProteusDialog, MessageBox


# --------------------------------------------------------------------------
# Class: ExportDialog
# Description: Class for the PROTEUS application print to pdf dialog form.
# Date: 14/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ExportDialog(ProteusDialog):
    """
    Class for the PROTEUS application print to pdf dialog form. It is used
    to display a dialog form with the print to pdf options.

    If the export strategy emits exportLogSignal (e.g. the output of the LaTeX
    engine), the text is shown in a panel below the export options.
    """

    # Maximum number of lines kept in the output panel and minimum width of
    # the dialog while the panel is shown
    LOG_MAX_LINES: int = 5000
    LOG_DIALOG_MIN_WIDTH: int = 720

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component. Store the page object and the controller instance.
        """
        super(ExportDialog, self).__init__(*args, **kwargs)

        # Export strategy
        self._export_strategy: ExportStrategy = None

        # True from the export button click until the export finishes
        self._exporting: bool = False

        # Time elapsed since the export button click, updated every second
        self._export_started: float = 0.0
        self._elapsed_timer: QTimer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._update_elapsed)

        # Widgets
        self.progress_bar: QProgressBar = None
        self.elapsed_label: QLabel = None
        self.log_label: QLabel = None
        self.log_view: QPlainTextEdit = None
        self.export_format_selector: QComboBox = None
        self.export_widget_holder: QVBoxLayout = None

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the component.
        """

        # Windows general settings ---------------------------------
        # Set the dialog title and width
        current_view = self._state_manager.get_current_view()
        self.setWindowTitle(_("export_dialog.title",_(f"xslt_templates.{current_view}")))
        self.sizeHint = lambda: QSize(400, 0)

        # Expand policy
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

        # Progress bar -------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        # self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        self.elapsed_label = QLabel()
        self.elapsed_label.hide()

        # Output of the export strategy, hidden until it emits some text
        self.log_label = QLabel(_("export_dialog.log.label"))
        self.log_label.hide()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_view.setMaximumBlockCount(self.LOG_MAX_LINES)
        self.log_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.log_view.setMinimumHeight(220)
        self.log_view.hide()

        # Export format selector ---------------------------------
        export_format_label = QLabel(_("export_dialog.export_strategy.label"))

        export_strategies: dict = Plugins().get_export_strategies()

        self.export_format_selector = QComboBox()
        for export_strategy_name, export_strategy_class in export_strategies.items():
            # e.g. LaTeX formats when the profile has no LaTeX template
            if not export_strategy_class.is_available(self._controller):
                continue
            self.export_format_selector.addItem(
                _(f"export_dialog.export_strategy.{export_strategy_name}"),
                export_strategy_class,
            )

        self.export_format_selector.currentIndexChanged.connect(
            self.update_export_strategy
        )

        # Specific export widget holder -----------------------------
        self.export_widget_holder = QVBoxLayout()
        self.export_widget_holder.setContentsMargins(0, 0, 0, 0)

        # Accept button
        self.accept_button.setText(_("dialog.export_button"))
        self.accept_button.setEnabled(False)
        self.accept_button.clicked.connect(self.export_button_clicked)

        self.reject_button.clicked.connect(self.close)

        # Main layout setup ---------------------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.elapsed_label)
        main_layout.addWidget(export_format_label)
        main_layout.addWidget(self.export_format_selector)
        main_layout.addLayout(self.export_widget_holder)
        main_layout.addWidget(self.log_label)
        main_layout.addWidget(self.log_view, 1)
        main_layout.addStretch()

        self.set_content_layout(main_layout)

        # First export strategy setup ---------------------------------
        self.export_format_selector.setCurrentIndex(0)
        self.export_format_selector.currentIndexChanged.emit(0)

    # ======================================================================
    # Dialog slots methods (connected to the component signals and helpers)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : update_export_strategy
    # Description: Update the export strategy when the export format is
    #              changed.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def update_export_strategy(self, index: int) -> None:
        """
        Update the export strategy when the export format is changed.
        The export strategy widget is replaced by the new one.

        Old export strategy must be deleted to disconnect the signals.
        """
        # Get the selected export format
        export_strategy_class: Callable = self.export_format_selector.currentData()

        # Update button box
        self.accept_button.setEnabled(False)

        # Delete the current export strategy
        # This is neccessary to disconnect the signals
        if self._export_strategy is not None:
            self._export_strategy.deleteLater()
            self._export_strategy = None

        # Clear the export widget holder
        for i in reversed(range(self.export_widget_holder.count())):
            self.export_widget_holder.itemAt(i).widget().setParent(None)

        # Update the export strategy ---------------------------------
        self._export_strategy = export_strategy_class(self._controller)

        # Setup new export strategy ---------------------------------
        # Strategy export widget
        export_widget: QWidget = self._export_strategy.exportFormWidget()
        self.export_widget_holder.addWidget(export_widget)

        # TODO: Find a way to resize the dialog to fit the export widget,
        #       resize() method does not work.

        # Connect strategy signals
        self._export_strategy.readyToExportSignal.connect(self.accept_button.setEnabled)
        self._export_strategy.exportFinishedSignal.connect(self.export_finished_dialog)
        self._export_strategy.exportProgressSignal.connect(self._progress_changed)
        self._export_strategy.exportLogSignal.connect(self._append_log)
        self._clear_log()

    # ----------------------------------------------------------------------
    # Method     : export_button_clicked
    # Description: Handle the export button click.
    # Date       : 22/01/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def export_button_clicked(self) -> None:
        """
        Handle the export button click. Disable the button box to avoid
        multiple exports and show the progress bar, and call the export
        strategy export method once the dialog has been laid out and painted
        again.
        """
        self._clear_log()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._start_elapsed()
        self._exporting = True
        # The strategy cannot be replaced while it is exporting
        self.export_format_selector.setEnabled(False)
        self.accept_button.setEnabled(False)

        # The dialog grows when the progress bar and the elapsed time are
        # shown. Its layout and its painting are pending events, which are
        # processed (but not the user input) before the strategy starts to
        # work: an export that does all its work at once (e.g. the export to
        # HTML) does not return to the event loop until it finishes, and the
        # new area would be shown black meanwhile. Returning to the event
        # loop is not enough, since the timer fires before the window is
        # painted.
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        QTimer.singleShot(0, self._start_export)

    # ----------------------------------------------------------------------
    # Method     : _start_export
    # Description: Call the export strategy export method.
    # Date       : 14/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _start_export(self) -> None:
        """
        Call the export strategy export method, unless the dialog was closed
        (and the export cancelled) since the export button was clicked.
        """
        if self._exporting and self._export_strategy is not None:
            self._export_strategy.export()

    # ----------------------------------------------------------------------
    # Method     : print_pdf_finished_dialog
    # Description: Show a dialog when the export is finished.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def export_finished_dialog(self, filePath: str, success: bool) -> None:
        """
        Show a dialog when the export is finished.

        :param filePath: The path to the exported file.
        :param success: True if the export was successful, False otherwise.
        """
        self._exporting = False
        self._elapsed_timer.stop()

        if success:
            MessageBox.information(
                _("export_dialog.finished.dialog.title"),
                _("export_dialog.finished.dialog.text", filePath),
            )

            self.close()
        else:
            MessageBox.critical(
                _("export_dialog.finished.dialog.error.title"),
                _("export_dialog.finished.dialog.error.text"),
            )

            # The dialog stays open, so that the user can read the output of
            # the export (if any) and try again
            self.progress_bar.hide()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.export_format_selector.setEnabled(True)
            self.accept_button.setEnabled(True)

    # ----------------------------------------------------------------------
    # Method     : done
    # Description: Cancel a running export when the dialog is closed.
    # Date       : 08/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def done(self, result: int) -> None:
        """
        Every way of closing the dialog ends here: the cancel button and the
        window close button (through closeEvent and reject) and the Escape
        key (reject). If an export is running, it is cancelled, so that no
        process or temporary file is left behind.
        """
        self._elapsed_timer.stop()

        if self._exporting and self._export_strategy is not None:
            self._exporting = False
            self._export_strategy.cancel()

        super().done(result)

    # ----------------------------------------------------------------------
    # Method     : _progress_changed
    # Description: Handle the export progress signal.
    # Date       : 26/02/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def _progress_changed(self, progress: int) -> None:
        """
        Handle the export progress signal.

        :param progress: The export progress in percentage, or
                         ExportStrategy.PROGRESS_BUSY if it is not known.
        """
        if progress == ExportStrategy.PROGRESS_BUSY:
            # Unknown progress: the bar is animated, without a percentage
            self.progress_bar.setRange(0, 0)
            return

        progress = min(100, max(0, progress))
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)

    # ----------------------------------------------------------------------
    # Method     : _append_log
    # Description: Handle the export log signal.
    # Date       : 13/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _append_log(self, text: str) -> None:
        """
        Handle the export log signal: add the text at the end of the output
        panel, showing it the first time. The panel scrolls to the end unless
        the user has scrolled up to read it.

        :param text: Text to add to the panel.
        """
        if not text:
            return

        if self.log_view.isHidden():
            self.log_label.show()
            self.log_view.show()
            self.setMinimumWidth(self.LOG_DIALOG_MIN_WIDTH)
            self.adjustSize()

        scroll_bar = self.log_view.verticalScrollBar()
        at_end: bool = scroll_bar.value() >= scroll_bar.maximum() - 4

        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)

        if at_end:
            scroll_bar.setValue(scroll_bar.maximum())

    # ----------------------------------------------------------------------
    # Method     : _start_elapsed
    # Description: Start showing the time elapsed since the export started.
    # Date       : 13/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _start_elapsed(self) -> None:
        """
        Start showing the time elapsed since the export started. The label
        changes every second, so that the user can see that the application
        is working even if the export strategy has nothing to say.
        """
        self._export_started = time.monotonic()
        self._update_elapsed()
        self.elapsed_label.show()
        self._elapsed_timer.start()

    # ----------------------------------------------------------------------
    # Method     : _update_elapsed
    # Description: Update the elapsed time label.
    # Date       : 13/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _update_elapsed(self) -> None:
        """
        Update the elapsed time label (minutes and seconds).
        """
        seconds: int = int(time.monotonic() - self._export_started)
        self.elapsed_label.setText(
            _("export_dialog.elapsed", f"{seconds // 60}:{seconds % 60:02d}")
        )

    # ----------------------------------------------------------------------
    # Method     : _clear_log
    # Description: Empty and hide the output panel.
    # Date       : 13/10/2026
    # Version    : 0.1
    # Author     : Amador Durán Toro
    # ----------------------------------------------------------------------
    def _clear_log(self) -> None:
        """
        Empty the output panel and hide it until the export strategy emits
        some text again.
        """
        self.log_view.clear()
        self.log_label.hide()
        self.log_view.hide()

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog (static)
    # Description: Handle the creation and display of the form window.
    # Date       : 14/07/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(controller: Controller) -> "ExportDialog":
        """
        Handle the creation and display of the form window.

        :param controller: The application controller.
        """
        form_window = ExportDialog(controller=controller)
        form_window.exec()
        return form_window
