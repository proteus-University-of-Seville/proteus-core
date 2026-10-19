# ==========================================================================
# File: test_property_dialog_width.py
# Description: pytest file for the width of the property dialog, which is
#              widened to show all its category tabs
# Date: 18/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtWidgets import QTabWidget

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.views.components.main_window import MainWindow
from proteus.views.components.dialogs import property_dialog
from proteus.views.components.dialogs.property_dialog import PropertyDialog
from proteus.tests.end2end.fixtures import app, load_project

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

# Initial width of the dialog (see PropertyDialog.create_component)
INITIAL_WIDTH: int = 500


def open_dialog_with_long_tab_names(main_window: MainWindow, mocker, qtbot) -> PropertyDialog:
    """
    Open the property dialog of the first document of the test project,
    translating its category names into long texts so that its tabs do not
    fit in the initial width of the dialog.
    """
    load_project(main_window=main_window)
    controller = main_window._controller
    document_id = controller.get_current_project().get_descendants()[0].id

    translate = property_dialog._

    def long_category_names(key: str, *args, **kwargs) -> str:
        if key.startswith("archetype.prop_category."):
            # Long enough to exceed the initial width with a few tabs, short
            # enough not to reach the limit of the dialog width
            return f"Long category name {key.rsplit('.', 1)[-1]}"
        return translate(key, *args, **kwargs)

    mocker.patch.object(property_dialog, "_", side_effect=long_category_names)

    dialog = PropertyDialog(element_id=document_id, controller=controller)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    qtbot.waitUntil(lambda: dialog.width_fitted_to_tabs)
    return dialog


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_dialog_widened_to_show_all_tabs(app, mocker, qtbot):
    """
    The dialog is widened so that the tab bar shows all its tabs without
    scroll buttons.
    """
    dialog = open_dialog_with_long_tab_names(app, mocker, qtbot)
    tab_bar = dialog.findChild(QTabWidget).tabBar()

    qtbot.waitUntil(lambda: tab_bar.width() >= tab_bar.sizeHint().width())
    assert dialog.width() > INITIAL_WIDTH, "The dialog was not widened"
    assert (
        tab_bar.width() >= tab_bar.sizeHint().width()
    ), f"The tabs do not fit: {tab_bar.width()} < {tab_bar.sizeHint().width()}"


@pytest.mark.parametrize("fraction", [0.1, 0.3])
def test_dialog_width_is_limited(app, mocker, qtbot, fraction):
    """
    The dialog is not widened beyond a fraction of the available screen
    width, and it is never narrowed below its initial width.
    """
    mocker.patch.object(property_dialog, "MAX_SCREEN_WIDTH_FRACTION", fraction)
    dialog = open_dialog_with_long_tab_names(app, mocker, qtbot)

    screen_width = dialog.screen().availableGeometry().width()
    expected = max(INITIAL_WIDTH, int(screen_width * fraction))

    assert (
        dialog.width() <= expected
    ), f"Dialog width {dialog.width()} exceeds the limit {expected}"
    assert dialog.width() >= INITIAL_WIDTH, "The dialog was narrowed"
