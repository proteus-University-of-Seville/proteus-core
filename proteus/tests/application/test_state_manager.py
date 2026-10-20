# ==========================================================================
# File: test_state_manager.py
# Description: tests of the selection state of the documents
# ==========================================================================

from proteus.application.state.manager import StateManager


def test_select_object_of_a_document_not_shown_yet():
    # After opening a project the state is cleared; navigating to an object of
    # a document that has not been shown yet (e.g. the target of a symbolic
    # link in another document) must not fail
    state = StateManager()
    state.clear()
    state.set_current_document("doc-1")

    state.set_current_object("object-2", "doc-2", navigate=False)

    assert state.current_object["doc-2"] == "object-2"
    state.set_current_document("doc-2")
    assert state.get_current_object() == "object-2"
    state.clear()
