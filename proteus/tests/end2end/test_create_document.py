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


def test_create_document_from_a_project_archetype(app):
    """
    The documents of the project archetypes are offered in the new document
    dialog, with the project archetype they come from, and a document can be
    created from them.
    """
    main_window: MainWindow = app
    load_project(main_window=main_window, project_name=PROJECT_NAME)

    dialog: NewDocumentDialog = get_dialog(main_window.main_menu.add_document_button.click)
    combo = dialog.archetype_combo
    items = [(combo.itemText(i), combo.itemData(i)) for i in range(combo.count())]

    # Documents of project archetypes: key '<project archetype>/<document id>'
    # and the project archetype in the text
    from_projects = [(text, key) for text, key in items if "/" in key]
    assert from_projects, f"No documents of project archetypes in the dialog: {items}"
    assert all("(" in text and "»" in text for text, _ in from_projects), from_projects
    # Document archetypes go first
    assert items[: len(items) - len(from_projects)] == [
        item for item in items if "/" not in item[1]
    ]

    # Create a document from the empty one, which has no assets, so that the
    # sample project is not modified (assets are copied when the document is
    # created)
    text, key = next(item for item in from_projects if item[1].endswith("/empty-doc"))
    combo.setCurrentIndex(combo.findData(key))
    archetype = main_window._controller.get_archetype_by_id(key)
    dialog.accept_button.click()

    documents = main_window._controller.get_current_project().get_descendants()
    assert len(documents) == 1
    assert (
        documents[0].get_property(":Proteus-name").value
        == archetype.get_property(":Proteus-name").value
    )
    assert documents[0].id != archetype.id
