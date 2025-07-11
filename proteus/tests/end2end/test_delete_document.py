# ==========================================================================
# File: test_delete_document.py
# Description: pytest file for the PROTEUS pyqt delete document use case
# Date: 16/08/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import QPoint

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.views.components.dialogs.delete_dialog import DeleteDialog
from proteus.views.components.dialogs.context_menu import ContextMenu
from proteus.views.components.documents_container import DocumentsContainer
from proteus.views.components.document_tree import DocumentTree
from proteus.views.components.main_window import MainWindow
from proteus.tests.end2end.fixtures import app, load_project, get_dialog, get_context_menu
from proteus.tests.fixtures import SampleData

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

PROJECT_NAME = "one_doc_project"
DOCUMENT_ID = SampleData.get("document_to_render", project_name=PROJECT_NAME)

# --------------------------------------------------------------------------
# End to end "delete document" tests
# --------------------------------------------------------------------------


def test_delete_document(app):
    """
    Test the delete document use case. Delete the only document in an
    project. It tests the following steps:
        - Open the confirmation dialog
        - Confirm the dialog

    Checks:
        - Document is deleted
        - Main menu buttons state
        - State manager document and object
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

    # Dialog handling and delete button click
    delete_document_button = main_window.main_menu.delete_document_button
    dialog: DeleteDialog = get_dialog(delete_document_button.click)
    dialog.accept_button.clicked.emit()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Check buttons state changed
    assert save_button_state != main_window.main_menu.save_button.isEnabled(), (
        "Save button state should change from DISABLED to ENABLED when a document is deleted"
        f"Current state: {main_window.main_menu.save_button.isEnabled()}"
    )
    assert (
        delete_doc_button_state
        != main_window.main_menu.delete_document_button.isEnabled()
    ), (
        "Delete document button state should change from ENABLED to DISABLED when a document is deleted and there are no more documents in the project"
        f"Current state: {main_window.main_menu.delete_document_button.isEnabled()}"
    )
    assert (
        export_doc_button_state
        != main_window.main_menu.export_view_button.isEnabled()
    ), (
        "Export document button state should change from ENABLED to DISABLED when a document is deleted and there are no more documents in the project"
        f"Current state: {main_window.main_menu.export_view_button.isEnabled()}"
    )
    assert (
        undo_button_state != main_window.main_menu.undo_button.isEnabled()
    ), (
        "Undo button state should change from DISABLED to ENABLED when a document is deleted in a project"
        f"Current state: {main_window.main_menu.undo_button.isEnabled()}"
    )

     # Check documents container does not include the document -------------------------------------------
    documents_container = main_window.project_container.documents_container
    assert (
        documents_container.tabs.keys().__len__() == 0
    ), f"Documents container should not include any document tab, number of tabs: '{documents_container.tabs.keys().__len__()}'"

    # Check that the tab was deleted from the tabbar
    tab_bar = documents_container.tabBar()
    assert (
        tab_bar.count() == 0
    ), f"Documents container tab bar should not include any tab, number of tabs: '{tab_bar.count()}'"

    # Check state manager current document and object are none -------------------------------------------
    assert (
        main_window._state_manager.get_current_document() is None
    ), "Current document in state manager should be None"
    assert (
        main_window._state_manager.get_current_object() is None
    ), "Current object in state manager should be None"


def test_delete_document_contextmenu(app):
    """
    Test the delete document use case using the context menu button. Delete the only document in an
    project. It tests the following steps:
        - Open the confirmation dialog
        - Confirm the dialog

    Checks:
        - Document is deleted
        - Main menu buttons state
        - State manager document and object
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
    documents_container: DocumentsContainer = (
        main_window.project_container.documents_container
    )

    # Right click arrange
    # NOTE: Clicking in a QMenu is not supported by pytest-qt
    # https://github.com/pytest-dev/pytest-qt/issues/195
    document_tree: DocumentTree = documents_container.tabs[DOCUMENT_ID]
    doc_tree_element: QTreeWidgetItem = document_tree.tree_items[DOCUMENT_ID]
    document_tree.setCurrentItem(doc_tree_element)

    # Trigger context menu
    element_position: QPoint = document_tree.visualItemRect(doc_tree_element).center()
    context_menu: ContextMenu = get_context_menu(
        lambda: document_tree.customContextMenuRequested.emit(element_position)
    )

    # Dialog handling
    dialog: DeleteDialog = get_dialog(context_menu.action_delete_object.trigger)
    dialog.accept_button.clicked.emit()

    # --------------------------------------------
    # Assert
    # --------------------------------------------

    # Check buttons state changed
    assert save_button_state != main_window.main_menu.save_button.isEnabled(), (
        "Save button state should change from DISABLED to ENABLED when a document is deleted"
        f"Current state: {main_window.main_menu.save_button.isEnabled()}"
    )
    assert (
        delete_doc_button_state
        != main_window.main_menu.delete_document_button.isEnabled()
    ), (
        "Delete document button state should change from ENABLED to DISABLED when a document is deleted and there are no more documents in the project"
        f"Current state: {main_window.main_menu.delete_document_button.isEnabled()}"
    )
    assert (
        export_doc_button_state
        != main_window.main_menu.export_view_button.isEnabled()
    ), (
        "Export document button state should change from ENABLED to DISABLED when a document is deleted and there are no more documents in the project"
        f"Current state: {main_window.main_menu.export_view_button.isEnabled()}"
    )
    assert (
        undo_button_state != main_window.main_menu.undo_button.isEnabled()
    ), (
        "Undo button state should change from DISABLED to ENABLED when a document is deleted in a project"
        f"Current state: {main_window.main_menu.undo_button.isEnabled()}"
    )

     # Check documents container does not include the document -------------------------------------------
    documents_container = main_window.project_container.documents_container
    assert (
        documents_container.tabs.keys().__len__() == 0
    ), f"Documents container should not include any document tab, number of tabs: '{documents_container.tabs.keys().__len__()}'"

    # Check that the tab was deleted from the tabbar
    tab_bar = documents_container.tabBar()
    assert (
        tab_bar.count() == 0
    ), f"Documents container tab bar should not include any tab, number of tabs: '{tab_bar.count()}'"

    # Check state manager current document and object are none -------------------------------------------
    assert (
        main_window._state_manager.get_current_document() is None
    ), "Current document in state manager should be None"
    assert (
        main_window._state_manager.get_current_object() is None
    ), "Current object in state manager should be None"

