# ==========================================================================
# File: test_export_comments.py
# Description: pytest file for leaving the comments out of the exports
# Date: 20/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import shutil
from configparser import ConfigParser
from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.application.configuration.app_settings import AppSettings
from proteus.application.configuration.config import Config
from proteus.application.state.manager import StateManager
from proteus.application.resources.plugins import Plugins
from proteus.views.components.dialogs.export_dialog import ExportDialog
from proteus.tests.end2end.fixtures import app, load_project

# --------------------------------------------------------------------------
# Test specific constants
# --------------------------------------------------------------------------

TEST_PROJECT_NAME = "example_project"
TEST_DOCUMENT_ID = "SS2yr44xAPqq"
COMMENT_ID = "test-comment"
COMMENT_XML = f"""<?xml version='1.0' encoding='UTF-8'?>
<object id="{COMMENT_ID}" classes="traceable-object paragraph comment" acceptedChildren=":Proteus-none" acceptedParents=":Proteus-any">
  <properties>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[Guidance]]></stringProperty>
    <markdownProperty name="text" category="general"><![CDATA[Text of the comment.]]></markdownProperty>
  </properties>
  <children/>
</object>
"""

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def project_with_comment(folder: Path) -> Path:
    """
    Copy of the example project with a comment as the first child of its
    first document.
    """
    project = folder / TEST_PROJECT_NAME
    shutil.copytree(PROTEUS_SAMPLE_PROJECTS_PATH / TEST_PROJECT_NAME, project)
    (project / "objects" / f"{COMMENT_ID}.xml").write_text(COMMENT_XML, encoding="utf-8")

    document_file = project / "objects" / f"{TEST_DOCUMENT_ID}.xml"
    document = ET.parse(str(document_file))
    children = document.getroot().find("children")
    children.insert(0, ET.Element("child", id=COMMENT_ID))
    document.write(str(document_file), xml_declaration=True, encoding="UTF-8")
    return project


def object_ids(xml: ET._Element) -> set:
    return {element.get("id") for element in xml.iter("object")}

# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_project_xml_without_comments(app, tmp_path):
    """
    The project XML leaves out the objects of the excluded classes, and
    keeps all the other objects.
    """
    project = project_with_comment(tmp_path)
    app._controller.load_project(str(project))
    service = app._controller._project_service

    with_comments = service.generate_project_xml()
    without_comments = service.generate_project_xml(excluded_classes=("comment",))

    assert COMMENT_ID in object_ids(with_comments)
    assert object_ids(without_comments) == object_ids(with_comments) - {COMMENT_ID}


def test_rendered_views_with_and_without_comments(app, tmp_path):
    """
    The renders used by the exports (HTML view and any template) include the
    comments unless include_comments is False.
    """
    project = project_with_comment(tmp_path)
    controller = app._controller
    controller.load_project(str(project))
    StateManager().set_current_document(TEST_DOCUMENT_ID)

    # XSLT functions are added to the render service by app.py at start-up
    controller._render_service.add_functions_to_namespace(Plugins().get_xslt_functions())

    assert COMMENT_ID in controller.get_html_view("default")
    assert COMMENT_ID not in controller.get_html_view("default", include_comments=False)

    # LaTeX template (used by the LaTeX and PDF from LaTeX exports)
    assert "Text of the comment" in controller.render_template("latex")
    assert "Text of the comment" not in controller.render_template("latex", include_comments=False)


def test_export_include_comments_setting(tmp_path):
    """
    The choice is remembered in the session section of the settings file,
    and it is True if it was never made.
    """
    settings = AppSettings.__new__(AppSettings)
    settings.config_parser = ConfigParser()
    settings.settings_file_path = tmp_path / "proteus.ini"

    assert settings.get_export_include_comments() is True

    settings.set_export_include_comments(False)
    saved = ConfigParser()
    saved.read(settings.settings_file_path)

    assert settings.get_export_include_comments() is False
    assert saved.getboolean("session", "export_include_comments") is False


def test_export_dialog_passes_and_remembers_the_choice(app, monkeypatch):
    """
    The checkbox starts with the last choice; when exporting, the choice is
    given to the strategy and remembered, and the checkbox cannot change
    while the export runs.
    """
    load_project(main_window=app, project_name=TEST_PROJECT_NAME)
    StateManager().set_current_document(TEST_DOCUMENT_ID)

    remembered = []
    settings = Config().app_settings
    monkeypatch.setattr(settings, "get_export_include_comments", lambda: False)
    monkeypatch.setattr(settings, "set_export_include_comments", remembered.append)

    dialog = ExportDialog(controller=app._controller)
    dialog._export_strategy.export = lambda: None

    assert not dialog.include_comments_checkbox.isChecked()

    dialog.include_comments_checkbox.setChecked(True)
    dialog.export_button_clicked()

    assert dialog._export_strategy.include_comments is True
    assert remembered == [True]
    assert not dialog.include_comments_checkbox.isEnabled()
    dialog.reject()
    dialog.deleteLater()
