# ==========================================================================
# File: test_create_document.py
# Description: pytest file for the PROTEUS pyqt create document use case
# Date: 15/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# NOTE: https://github.com/pytest-dev/pytest-qt/issues/37
# QApplication instace cannot be deleted. This might cause tests failures.

# NOTE: https://github.com/pytest-dev/pytest-qt/issues/256
# Dialog handling can interfere with running tests together. Workaround
# listed in the issue with 5ms delay in QTimer seems to work. Since
# dialogs are an important part of the app, this might be a problem
# in the future. No complete solution found yet.

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
from proteus.views.components.dialogs.new_document_dialog import NewDocumentDialog
from proteus.tests.end2end.fixtures import app, load_project, get_dialog

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

PROJECT_NAME = "empty_project"

# --------------------------------------------------------------------------
# End to end "create document" tests
# --------------------------------------------------------------------------


def test_create_document(app):
    """
    Test the create document use case. Create a document in an existing
    project. It tests the following steps:
        - Open the create document dialog
        - Create a new document

    Checks:
        - Main menu buttons state
        - Document was created
        - Document was selected
        - No object is selected in the new document
    """
    # --------------------------------------------
    # Arrange
    # --------------------------------------------
    main_window: MainWindow = app

    load_project(main_window=main_window, project_name=PROJECT_NAME)

    # Buttons that should change state when document is created in an empty project
    save_button_state = main_window.main_menu.save_button.isEnabled()
    delete_doc_button_state = main_window.main_menu.delete_document_button.isEnabled()
    export_doc_button_state = main_window.main_menu.export_view_button.isEnabled()
    undo_button_state = main_window.main_menu.undo_button.isEnabled()

    # --------------------------------------------
    # Act
    # --------------------------------------------

    # Add document button click
    add_document_button = main_window.main_menu.add_document_button
    dialog: NewDocumentDialog = get_dialog(add_document_button.click)
    dialog.accept_button.click()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Check buttons state changed
    assert save_button_state != main_window.main_menu.save_button.isEnabled(), (
        "Save button state should change from DISABLED to ENABLED when a document is created in an empty project"
        f"Current state: {main_window.main_menu.save_button.isEnabled()}"
    )
    assert (
        delete_doc_button_state
        != main_window.main_menu.delete_document_button.isEnabled()
    ), (
        "Delete document button state should change from DISABLED to ENABLED when a document is created in an empty project"
        f"Current state: {main_window.main_menu.delete_document_button.isEnabled()}"
    )
    assert (
        export_doc_button_state
        != main_window.main_menu.export_view_button.isEnabled()
    ), (
        "Export document button state should change from DISABLED to ENABLED when a document is created in an empty project"
        f"Current state: {main_window.main_menu.export_view_button.isEnabled()}"
    )
    assert (
        undo_button_state != main_window.main_menu.undo_button.isEnabled()
    ), (
        "Undo button state should change from DISABLED to ENABLED when a document is created in an empty project"
        f"Current state: {main_window.main_menu.undo_button.isEnabled()}"
    )

     # Check documents container includes the new document -------------------------------------------
    documents_container = main_window.project_container.documents_container
    assert (
        documents_container.tabs.keys().__len__() == 1
    ), f"Documents container has not only one tab, number of tabs: '{documents_container.tabs.keys().__len__()}'"

    # Check each document tree has at least one tree item
    for document_tree in documents_container.tabs.values():
        assert (
            document_tree.__class__.__name__ == "DocumentTree"
        ), f"Document tree is not a DocumentTree, '{document_tree.__class__.__name__}'"
        assert (
            document_tree.tree_items.keys().__len__() >= 1
        ), f"Document tree has not at least one tree item, number of tree items: '{document_tree.tree_items.keys().__len__()}'"

    # Check the new document is selected -----------------------------------------------------------
    assert (
        main_window._state_manager.get_current_document() == list(documents_container.tabs.keys())[0]
    ), "The new document is not the selected document in the state manager"

    # Check no object is selected in the state manager
    assert (
        main_window._state_manager.get_current_object() is None
    ), "No object should be selected in the new document"

