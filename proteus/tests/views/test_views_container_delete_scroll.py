# ==========================================================================
# File: test_views_container_delete_scroll.py
# Description: pytest file for the scroll target after deleting an object
# Date: 09/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from types import SimpleNamespace

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model.abstract_object import ProteusState
from proteus.views.components.views_container import ViewsContainer


def _object(id, state=ProteusState.CLEAN, parent=None):
    return SimpleNamespace(id=id, state=state, parent=parent, children=[])


def _scroll_target(states):
    """
    Build a parent with children with the given states, delete the one with
    id "x" and return the id passed to display_view.
    """
    parent = _object("parent")
    parent.children = [_object(id, state, parent) for id, state in states]
    scrolled = []
    container = SimpleNamespace(
        _controller=SimpleNamespace(
            get_element=lambda id: next(c for c in parent.children if c.id == id)
        ),
        display_view=lambda id: scrolled.append(id),
    )
    ViewsContainer.update_view_on_delete_object(container, "x", True)
    return scrolled


DEAD = ProteusState.DEAD


def test_scrolls_to_previous_sibling():
    assert _scroll_target([("a", None), ("b", None), ("x", DEAD), ("c", None)]) == ["b"]


def test_ignores_dead_siblings():
    assert _scroll_target([("a", None), ("d", DEAD), ("x", DEAD)]) == ["a"]


def test_scrolls_to_next_sibling_if_first():
    assert _scroll_target([("d", DEAD), ("x", DEAD), ("c", None)]) == ["c"]


def test_scrolls_to_parent_if_only_child():
    assert _scroll_target([("x", DEAD)]) == ["parent"]


def test_no_update_if_flag_is_false():
    container = SimpleNamespace(display_view=lambda id: 1 / 0)
    ViewsContainer.update_view_on_delete_object(container, "x", False)
