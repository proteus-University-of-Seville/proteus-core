# ==========================================================================
# File: test_export_dialog.py
# Description: pytest file for the PROTEUS pyqt info fialog
# Date: 29/01/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================


# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.views.components.main_window import MainWindow
from proteus.views.components.dialogs.export_dialog import ExportDialog
from proteus.tests.end2end.fixtures import app, get_dialog, load_project


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

TEST_PROJECT_NAME = "empty_project"

# --------------------------------------------------------------------------
# End to end "export dialog" tests
# --------------------------------------------------------------------------


def test_export_dialog(app):
    """
    Test the creation of the export dialog. Export strategies and dialog
    general behaviour may be tested in views tests.
    """

    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    load_project(main_window=main_window)

    export_button = main_window.main_menu.export_view_button

    # --------------------------------------------
    # Act
    # --------------------------------------------

    dialog: ExportDialog = get_dialog(export_button.click)

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    assert isinstance(
        dialog, ExportDialog
    ), f"Export dialog must be instance of ExportDialog but it is {type(dialog)}"

    assert (
        dialog.accept_button.isEnabled() == False
    ), "Export button must be disabled by default"
