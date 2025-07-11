# ==========================================================================
# File: test_open_project.py
# Description: pytest file for the PROTEUS pyqt main window
# Date: 11/08/2023
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

from proteus.model import PROJECT_FILE_NAME
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.views.components.main_window import MainWindow
from proteus.tests.end2end.fixtures import app

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

SAMPLE_PROJECT_PATH = PROTEUS_SAMPLE_PROJECTS_PATH / "example_project" / PROJECT_FILE_NAME


# --------------------------------------------------------------------------
# End to end "open project" tests
# --------------------------------------------------------------------------


def test_open_project(mocker, app):
    """
    Test the open project use case. Opens a project with documents and objects.
    It tests the following:
        - The main window title changes to include the project name
        - The main window central widget changes to a ProjectContainer
        - The expected buttons become enabled/disabled
        - Documents container is created and populated
        - Document trees are created and populated
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    # Mock the QFileDialog response and handle the dialog life cycle
    mocker.patch(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        return_value=[SAMPLE_PROJECT_PATH.as_posix()],
    )

    # Store previous information
    old_window_title = main_window.windowTitle()
    old_central_widget = main_window.centralWidget()

    # --------------------------------------------
    # Act
    # --------------------------------------------
    # Open project button click
    open_project_button = main_window.main_menu.open_button
    open_project_button.click()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Check title changed to include project name
    assert (
        main_window.windowTitle() != old_window_title
    ), f"Expected window title to change from {old_window_title}"
    assert old_window_title in main_window.windowTitle(), (
        f"Expected window title to include {old_window_title} as prefix"
        f"current title {main_window.windowTitle()}"
    )

    # Check central widget change to project container
    assert (
        main_window.centralWidget() != old_central_widget
    ), "Central widget should have been deleted and replaced by a new one"
    assert (
        main_window.centralWidget().__class__.__name__ == "ProjectContainer"
    ), f"Expected central widget to be a ProjectContainer, got {main_window.centralWidget().__class__.__name__}"

    # Check main menu buttons new state
    assert (
        main_window.main_menu.project_properties_button.isEnabled()
    ), "Expected edit project properties button to be enabled"
    assert (
        main_window.main_menu.add_document_button.isEnabled()
    ), "Expected add document button to be enabled"
    assert (
        main_window.main_menu.delete_document_button.isEnabled()
    ), "Expected delete document button to be enabled"
    assert (
        main_window.main_menu.export_view_button.isEnabled()
    ), "Expected export document button to be enabled"

    # Check documents container
    documents_container = main_window.project_container.documents_container
    assert (
        documents_container.__class__.__name__ == "DocumentsContainer"
    ), f"Expected documents container to be a DocumentsContainer, got {documents_container.__class__.__name__}"

    # Expected documents
    expected_doc_number: int = main_window._controller.get_current_project().get_descendants().__len__()

    # Check documents container tabs and tree chidlren correspond
    assert (
        documents_container.tabs.keys().__len__() == expected_doc_number
    ), f"Expected {expected_doc_number} tabs, got {documents_container.tabs.keys().__len__()}"

    # Check each document tree has at least one tree item
    for document_tree in documents_container.tabs.values():
        assert (
            document_tree.__class__.__name__ == "DocumentTree"
        ), f"Expected document tree to be a DocumentTree, got {document_tree.__class__.__name__}"
        assert (
            document_tree.tree_items.keys().__len__() >= 1
        ), f"Expected at least one tree item, got {document_tree.tree_items.keys().__len__()}"


