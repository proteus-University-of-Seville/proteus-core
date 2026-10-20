# ==========================================================================
# File: test_export_html.py
# Description: pytest file for the export to HTML of a view that references
#              the resources of other templates
# Date: 19/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.plugins import Plugins
from proteus.application.state.manager import StateManager
from proteus.tests.end2end.fixtures import app, load_project

PLUGIN_DIR = Path("resources/plugins").resolve()
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from basic.export.export_html import REFERENCED_TEMPLATES_FOLDER, referenced_templates  # noqa: E402

# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_referenced_templates():
    """
    The templates referenced by the HTML are found, without the current view
    and without repetitions.
    """
    html = (
        '<link href="templates:///default/resources/css/default.css"/>'
        '<img src="templates:///default/resources/images/logo.png"/>'
        '<script src="templates:///other/resources/javascript/x.js"></script>'
        '<link href="templates:///view/resources/css/view.css"/>'
    )
    assert referenced_templates(html, "view") == ["default", "other"]
    assert referenced_templates("<p>no templates</p>", "view") == []


def test_export_copies_referenced_templates(app, tmp_path, monkeypatch):
    """
    A view that uses the resources of another template (here, the 'latex'
    view using the CSS of the 'default' template) is exported with a copy of
    that template in 'templates/<name>' and its URLs point to it. A reference
    to a template that does not exist does not make the export fail.
    """
    load_project(main_window=app)
    controller = app._controller
    StateManager().set_current_view("latex")

    html = (
        "<html><head>"
        '<link rel="stylesheet" href="templates:///default/resources/css/default.css"/>'
        '<link rel="stylesheet" href="templates:///missing/resources/css/missing.css"/>'
        "</head><body></body></html>"
    )
    monkeypatch.setattr(controller, "get_html_view", lambda view, include_comments=True: html)

    strategy = Plugins().get_export_strategies()["html"](controller)
    strategy.exportFormWidget()
    strategy._path_input.setDirectory(str(tmp_path))
    strategy._folder_name_input.setText("export")

    results = []
    strategy.exportFinishedSignal.connect(lambda path, success: results.append(success))
    strategy.export()

    assert results == [True], "The export failed"

    export_folder = tmp_path / "export"
    copied_css = export_folder / REFERENCED_TEMPLATES_FOLDER / "default" / "resources" / "css" / "default.css"
    assert copied_css.exists(), "The resources of the referenced template were not copied"
    assert not list((export_folder / REFERENCED_TEMPLATES_FOLDER / "default").rglob("*.xsl")), \
        "XSL files of the referenced template were copied"

    exported_html = (export_folder / "index.html").read_text(encoding="utf-8")
    assert f'href="./{REFERENCED_TEMPLATES_FOLDER}/default/resources/css/default.css"' in exported_html
    assert "templates:///default/" not in exported_html
