"""Rendered comparison tests using Chromium and actual project templates."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from proteus.application.resources.plugins import Plugins
from proteus.application.state.manager import StateManager
from proteus.tests.end2end.fixtures import app
from proteus.tests.end2end.test_git_controls import open_repository
from proteus.tests.services.test_git_operations import isolated_git_config
from proteus.views.components.git_document_review import GitRenderedReview


def js(browser, script, qtbot):
    values = []
    browser.page().runJavaScript(script, values.append)
    qtbot.waitUntil(lambda: bool(values), timeout=15000)
    return values[0]


def render_setup(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    app._controller._render_service.add_functions_to_namespace(Plugins().get_xslt_functions())
    root = service.document_revision('proteus.xml', 'HEAD')
    node = root.xpath('.//object[properties/*[@name="text"]]')[0]
    return service, root, node.get('id')


@pytest.mark.parametrize('kind', ['added', 'deleted', 'unicode'])
def test_rendered_diff_highlights_added_deleted_and_unicode_text(app, qtbot, tmp_path, kind):
    service, root, oid = render_setup(app, qtbot, tmp_path)
    before, after = deepcopy(root), deepcopy(root)
    before.xpath('.//object[@id=$oid]/properties/*[@name="text"]', oid=oid)[0].text = 'Hola 😀 antiguo'
    after.xpath('.//object[@id=$oid]/properties/*[@name="text"]', oid=oid)[0].text = 'Hola 😀 nuevo'
    roots = (None, after) if kind == 'added' else (before, None) if kind == 'deleted' else (before, after)
    state = StateManager()
    previous = (state.current_document, state.get_current_view())
    container = app.project_container.views_container
    review = GitRenderedReview(app._controller, roots, oid, False, lambda: None, container)
    container.setCurrentIndex(container.addTab(review, 'Review'))
    actual_side = 1 if kind == 'added' else 0
    qtbot.waitUntil(lambda: bool(review._rendered_text.get(actual_side)), timeout=15000)
    if kind == 'unicode':
        qtbot.waitUntil(lambda: len(review._rendered_text) == 2, timeout=15000)
    assert set(review._rendered_text) == {0, 1}
    sides = [1] if kind == 'added' else [0] if kind == 'deleted' else [0, 1]
    for side in sides:
        result = json.loads(js(review.browsers[side],
            'JSON.stringify({text:document.body.textContent, marks:Array.from(document.querySelectorAll("mark")).map(node=>node.textContent)})', qtbot))
        assert 'Hola 😀' in result['text']
        assert result['marks']
        assert ('antiguo' if side == 0 else 'nuevo') in ''.join(result['marks'])
    assert (state.current_document, state.get_current_view()) == previous
    assert not service.status().files
    assert not app._controller.check_unsaved_changes()


def test_large_rendered_comparison_loads_without_data_url_size_limit(app, qtbot, tmp_path, monkeypatch):
    service, root, oid = render_setup(app, qtbot, tmp_path)
    payload = 'A' * 2_100_000
    html = '<html><head></head><body><p id="' + oid + '">' + payload + '</p></body></html>'
    monkeypatch.setattr(app._controller._render_service, 'render', lambda *_: html)
    container = app.project_container.views_container
    review = GitRenderedReview(app._controller, (root, root), oid, False, lambda: None, container)
    container.setCurrentIndex(container.addTab(review, 'Large comparison'))
    qtbot.waitUntil(lambda: len(review._rendered_text) == 2, timeout=30000)
    assert all(len(value) == len(payload) for value in review._rendered_text.values())
    assert all(browser.url().isLocalFile() for browser in review.browsers)
    folder = Path(review._html_directory.path())
    assert (folder / '0.html').stat().st_size > 2_000_000


def test_history_detail_failures_and_stale_responses_keep_current_selection(app, qtbot, tmp_path, monkeypatch):
    from proteus.services.git_service import GitError
    from proteus.views.components.git_history import GitHistoryDialog
    from proteus.tests.services.test_git_operations import commit_file
    panel, service = open_repository(app, qtbot, tmp_path)
    commit_file(service, 'notes.txt', 'new commit', 'New commit')
    commits = service.history()
    monkeypatch.setattr(service, 'commit_details', lambda oid: (_ for _ in ()).throw(GitError('Cannot read this commit')))
    dialog = GitHistoryDialog(service, commits, panel)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: not dialog._jobs, timeout=15000)
    assert 'Cannot read this commit' in dialog.details.toPlainText()
    old = ('details', -1)
    current = dialog._requested
    dialog.loaded(old, 'stale result', None)
    assert dialog._requested == current
    assert 'stale result' not in dialog.details.toPlainText()
    dialog.loaded(current, 'current result', None)
    assert dialog.details.toPlainText() == 'current result'
    dialog.search.setText('no matching commit')
    assert not dialog.details.toPlainText()
    assert dialog._requested is None
