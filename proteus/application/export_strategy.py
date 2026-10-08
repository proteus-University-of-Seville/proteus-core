# ==========================================================================
# File: export_dialog.py
# Description: PROTEUS export strategy module.
# Date: 14/07/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from abc import ABC, abstractmethod

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import AbstractObjectMeta
from proteus.controller.command_stack import Controller


# --------------------------------------------------------------------------
# Class: ExportStrategy
# Description: Abstract class for the PROTEUS application export strategy.
# Date: 22/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class ExportStrategy(QObject, ABC, metaclass=AbstractObjectMeta):
    """
    Abstract class for the PROTEUS application export strategy.

    It defines the basic methods used by the export dialog to
    handle the export process. It also defines signals to communicate
    with the export dialog.
    - exportFinishedSignal: emitted when the export process has finished.
    it sends the path to the exported file and if it was successful.
    - readyToExportSignal: emitted when the export dialog is ready to
    to perform the export.
    - exportProgressSignal: emitted to update the progress of the export
    process (progress bar in the export dialog 0-100).

    Export strategies use Controller to access the backend information
    directly and perform the necessary operations to export the current
    view.
    """

    exportFinishedSignal = pyqtSignal(str, bool)
    readyToExportSignal = pyqtSignal(bool)
    exportProgressSignal = pyqtSignal(int)

    def __init__(self, controller: Controller) -> None:
        super().__init__()

        self._controller = controller

    @abstractmethod
    def export(self) -> None:
        """
        Export the current view.

        Must be implemented by the concrete export strategy.
        """
        pass

    @classmethod
    def is_available(cls, controller: Controller) -> bool:
        """
        Whether the strategy can be used with the current profile and
        project. The export dialog only lists available strategies.

        Strategies that depend on something the profile may not provide
        (e.g. a template with a given output format) should override it.
        By default it returns True.
        """
        return True

    def cancel(self) -> None:
        """
        Cancel a running export (e.g. the export dialog is closed before it
        finishes). exportFinishedSignal must not be emitted afterwards.

        Strategies whose export runs in the background (processes, worker
        threads) should override it to stop them and remove any partial
        output. By default it does nothing.
        """
        pass

    @abstractmethod
    def exportFormWidget(self) -> QWidget:
        """
        Widget that will be displayed in the export dialog form.

        Used to retrieve user input data neccesary to perform the export.

        Must be implemented by the concrete export strategy.
        """
        pass


    