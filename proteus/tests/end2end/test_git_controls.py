"""Qt integration: jobs complete in the UI thread and preserve document safety."""
import shutil
from pathlib import Path

from proteus.tests.end2end.fixtures import app
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.services.git_service import GitService
from proteus.tests.end2end.test_theme_switch_live import theme_state


def open_repository(app, qtbot, tmp_path):
    project = tmp_path / 'project'
    shutil.copytree(PROTEUS_SAMPLE_PROJECTS_PATH / 'example_project', project)
    service = GitService(project)
    service.run('init', '-b', 'develop')
    service.run('config', 'user.name', 'Test')
    service.run('config', 'user.email', 'test@example.invalid')
    service.run('add', '--', '.')
    service.commit('Initial')
    app._controller.load_project(str(project))
    panel = app.git_panel
    qtbot.waitUntil(lambda: panel.status is not None and not panel.busy, timeout=15000)
    return panel, service


def test_git_panel_detects_repository_and_updates_status(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    assert panel.status.branch == 'develop'
    assert not panel.commit_button.isEnabled()  # No staged files or message yet.
    assert 'develop' in panel.indicator.text()
    assert app.main_menu.tab_widget.tabText(app.main_menu.tab_widget.count() - 1) == 'Git'
    path = service.directory / 'new á.xml'
    path.write_text('<test/>', encoding='utf-8')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert any(f.path == path.name for f in panel.status.files)


def test_reload_replaces_model_and_resets_undo(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    before = app._controller.get_current_project()
    app._controller.reload_project_from_disk(str(service.directory))
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert app._controller.get_current_project() is not before
    assert app._controller.stack.isClean()
    assert not panel.blocked


def test_invalid_project_reload_keeps_previous_model(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    before = app._controller.get_current_project()
    (service.directory / 'proteus.xml').write_text('<<<<<<< invalid')
    panel.reload()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.blocked
    assert app._controller.get_current_project() is before
    assert not app.project_container.isEnabled()
    service.run('restore', '--', 'proteus.xml')
    panel.reload()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.blocked
    assert app.project_container.isEnabled()


def test_external_changes_pause_editor_until_reload(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    project_file = service.directory / 'proteus.xml'
    project_file.write_bytes(project_file.read_bytes() + b'\n')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.blocked
    assert not app.main_menu.isEnabled()
    panel.reload()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.blocked


def test_controller_refuses_writes_during_git_and_conflicts(app, qtbot, tmp_path):
    import pytest
    panel, service = open_repository(app, qtbot, tmp_path)
    controller = app._controller
    controller._git_operation_active = True
    with pytest.raises(RuntimeError):
        controller.save_project()
    controller._git_operation_active = False
    controller._git_write_blocked = True
    with pytest.raises(RuntimeError):
        controller.save_project()
    controller._git_write_blocked = False



def test_save_checks_external_changes_before_polling(app, qtbot, tmp_path):
    import pytest
    from proteus.services.git_service import GitError
    panel, service = open_repository(app, qtbot, tmp_path)
    path = service.directory / 'proteus.xml'
    changed = path.read_bytes() + b'\n'
    path.write_bytes(changed)
    with pytest.raises(GitError):
        app._controller.save_project()
    assert path.read_bytes() == changed
    assert panel.blocked


def test_importing_asset_does_not_look_like_an_external_document_edit(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    assets = service.directory / 'assets'
    assets.mkdir(exist_ok=True)
    (assets / 'new image.png').write_bytes(b'image')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.blocked
    app._controller.save_project()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)


def test_panel_stages_and_commits_only_selected_files(app, qtbot, tmp_path):
    from PyQt6.QtCore import Qt
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'selected.txt').write_text('include')
    (service.directory / 'other.txt').write_text('exclude')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    for group_index in range(panel.tree.topLevelItemCount()):
        group = panel.tree.topLevelItem(group_index)
        for index in range(group.childCount()):
            item = group.child(index)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0].path == 'selected.txt':
                item.setSelected(True)
    panel.stage()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    panel.message.setPlainText('Selected file only')
    panel.commit()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert service.run('log', '-1', '--format=%s').strip() == 'Selected file only'
    assert service.status().files[0].path == 'other.txt'
    assert panel.message.toPlainText() == ''


def test_panel_conflict_pauses_model_and_abort_recovers(app, qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    panel, service = open_repository(app, qtbot, tmp_path)
    notes = service.directory / 'notes.txt'
    notes.write_text('base\n')
    service.stage(['notes.txt'])
    service.commit('Notes')
    service.switch('other', create=True)
    notes.write_text('other\n')
    service.stage(['notes.txt'])
    service.commit('Other')
    service.switch('develop')
    notes.write_text('develop\n')
    service.stage(['notes.txt'])
    service.commit('Develop')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: None)
    monkeypatch.setattr(panel, 'show_output', lambda *args: None)
    monkeypatch.setattr(panel, 'confirm', lambda *args: True)
    panel.command(['merge', '--no-edit', 'other'], changes_disk=True, require_clean=True)
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.blocked
    assert panel.status.operation == 'merge'
    panel.abort_operation()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.blocked
    assert app.project_container.isEnabled()
    assert not panel.status.operation


def test_background_refresh_preserves_controls_selection_and_tree_items(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('notes')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    group = panel.tree.topLevelItem(2)
    item = group.child(0)
    item.setSelected(True)
    panel.message.setPlainText('Draft commit message')
    feedback = panel.feedback.text()
    panel.refresh()
    assert panel.busy
    assert panel.branch_button.isEnabled()
    assert panel.actions['push'].isEnabled()
    assert panel.message.isEnabled()
    assert panel.feedback.text() == feedback
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.tree.topLevelItem(2).child(0) is item
    assert item.isSelected()
    assert panel.message.toPlainText() == 'Draft commit message'
    assert panel.feedback.text() == feedback


def test_click_during_background_refresh_runs_after_query(app, qtbot, tmp_path):
    from threading import Event
    panel, service = open_repository(app, qtbot, tmp_path)
    gate = Event()
    calls = []
    panel.job(lambda: gate.wait(5), quiet=True)
    panel.guard(lambda: calls.append('clicked'))
    assert calls == []
    gate.set()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert calls == ['clicked']


def test_repository_context_is_visible_and_remote_credentials_are_hidden(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('remote', 'add', 'origin', 'https://fake-secret@github.com/team/project.git')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.repository_label.text() == service.directory.name
    assert panel.repository_path.full_text == str(service.directory)
    assert 'github.com/team/project' in panel.remote_label.text()
    assert 'fake-secret' not in panel.remote_label.text()
    assert 'fake-secret' not in panel.remote_label.toolTip()
    assert 'develop' in panel.indicator.text()
    assert all(not action.icon().isNull() for action in panel.actions.values())
    repository, branch = panel._ribbon_labels[0]
    assert repository.full_text == service.directory.name
    assert branch.full_text == 'develop'


def test_create_github_repository_can_open_browser_without_gh(app, qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtGui import QDesktopServices
    panel, service = open_repository(app, qtbot, tmp_path)
    monkeypatch.setattr(shutil, 'which', lambda name: None)
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)
    opened = []
    monkeypatch.setattr(QDesktopServices, 'openUrl', lambda url: opened.append(url.toString()))
    panel.publish_github()
    assert opened == ['https://github.com/new']


def test_clean_repository_has_only_one_empty_state_message(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    assert panel.summary_label.isHidden()
    assert not panel.empty_state.isHidden()
    assert panel.empty_state.text()


def test_git_icons_use_existing_application_resources(app, qtbot, tmp_path):
    from proteus.application.resources.icons import Icons, ProteusIconType
    from proteus.views.components.git_icons import git_icon
    panel, service = open_repository(app, qtbot, tmp_path)
    assert git_icon('commit', panel).cacheKey() == Icons().icon(ProteusIconType.MainMenu, 'save').cacheKey()
    assert git_icon('push', panel).cacheKey() == Icons().icon(ProteusIconType.App, 'context-menu-up').cacheKey()


def test_visual_history_selection_and_search(app, qtbot, tmp_path):
    from proteus.views.components.git_history import GitHistoryDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('added notes')
    service.stage(['notes.txt'])
    service.commit('Add notes')
    dialog = GitHistoryDialog(service, service.history(), panel)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.table.topLevelItemCount() == 2
    assert dialog.table.topLevelItem(0).text(1) == 'Add notes'
    qtbot.waitUntil(lambda: not dialog._jobs, timeout=15000)
    assert 'added notes' in dialog.details.toPlainText()
    dialog.table.setCurrentItem(dialog.table.topLevelItem(1))
    qtbot.waitUntil(lambda: not dialog._jobs, timeout=15000)
    assert 'Initial' in dialog.details.toPlainText()
    dialog.search.setText('Add notes')
    assert not dialog.table.topLevelItem(0).isHidden()
    assert dialog.table.topLevelItem(1).isHidden()
    assert dialog.table.isColumnHidden(0)
    dialog.search.clear()
    assert not dialog.table.isColumnHidden(0)
    dialog.close()


def test_branch_picker_search_and_keyboard_selection(app, qtbot, tmp_path):
    from PyQt6.QtCore import Qt
    from proteus.views.components.git_branches import GitBranchDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    service.create_branch('feature/search')
    service.switch('develop')
    service.run('tag', 'v1')
    dialog = GitBranchDialog(service.references(), 'develop', panel)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.search.setText('feature/search')
    assert dialog.list.count() == 4  # Three operations plus one matching branch.
    assert 'feature/search' in dialog.list.item(3).text()
    qtbot.keyClick(dialog.search, Qt.Key.Key_Return)
    assert dialog.choice[0] == 'reference'
    assert dialog.choice[1].name == 'feature/search'


def test_branch_checkout_reloads_project_and_success_has_no_ready_message(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    service.create_branch('feature')
    service.switch('develop')
    reference = next(ref for ref in service.references() if ref.name == 'feature')
    panel._checkout_reference(service, reference)
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.status.branch == 'feature'
    assert panel.feedback.text() == ''
    assert panel.feedback.isHidden()


def test_nested_project_header_uses_short_location_instead_of_warning(app, qtbot, tmp_path):
    from proteus.services.git_service import GitStatus
    panel, service = open_repository(app, qtbot, tmp_path)
    state = panel.status
    parent = service.directory.parent
    panel._show_status(GitStatus(parent, state.branch, '', 0, 0, state.files))
    assert service.directory.name in panel.scope_label.text()
    assert 'entire repository' not in panel.scope_label.text()
    assert not panel.scope_label.isHidden()


def test_repository_card_keeps_contrast_when_switching_themes(app, qtbot, tmp_path, theme_state):
    from PyQt6.QtGui import QPalette
    from proteus.application.resources.themes import ThemeService
    panel, service = open_repository(app, qtbot, tmp_path)
    panel.reveal()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    ThemeService().apply_theme('dark')
    qtbot.wait(50)
    assert panel.repository_card.grab().toImage().pixelColor(8, 8).lightness() < 100
    assert panel.repository_label.palette().color(QPalette.ColorRole.WindowText).lightness() > 150
    ThemeService().apply_theme('light')
    qtbot.wait(50)
    assert panel.repository_card.grab().toImage().pixelColor(8, 8).lightness() > 180


def test_status_bar_indicator_opens_branch_picker(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    calls = []
    monkeypatch.setattr(panel, 'choose_branch', lambda: calls.append('branches'))
    panel.indicator.click()
    assert calls == ['branches']


def test_saved_object_changes_show_names_highlight_and_navigate(app, qtbot, tmp_path):
    from proteus.application.events import GitChangesEvent
    from proteus.application.state.manager import StateManager
    from proteus.model import PROTEUS_NAME
    panel, service = open_repository(app, qtbot, tmp_path)
    obj = next(obj for obj in app._controller.get_objects() if 'paragraph' in obj.classes)
    name = obj.get_property(PROTEUS_NAME)
    app._controller.update_properties(obj.id, [name.clone('Changed paragraph title')])
    app._controller.save_project()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert obj.id in GitChangesEvent().changes
    entries = [panel.tree.topLevelItem(g).child(i) for g in range(panel.tree.topLevelItemCount())
               for i in range(panel.tree.topLevelItem(g).childCount())]
    assert any(item.text(0) == 'Changed paragraph title' for item in entries)
    file = next(file for file in panel.status.files if file.path.endswith(str(obj.id) + '.xml'))
    panel.navigate_to_file(file)
    assert StateManager().get_current_object() == obj.id
    panel.highlight_toggle.setChecked(False)
    assert GitChangesEvent().changes == {}
    panel.highlight_toggle.setChecked(True)
    assert obj.id in GitChangesEvent().changes
    panel.stage_reviewed_file(file)
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert any(file.index == 'M' for file in panel.status.files if file.path.endswith(str(obj.id) + '.xml'))


def test_object_changed_after_review_is_not_silently_staged(app, qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    panel, service = open_repository(app, qtbot, tmp_path)
    path = service.directory / 'notes.txt'
    path.write_text('reviewed')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    file = next(file for file in panel.status.files if file.path == 'notes.txt')
    reviewed = service.diff(file)
    path.write_text('changed after review')
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: None)
    panel.stage_reviewed_file(file, expected_diff=reviewed)
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert next(file for file in service.status().files if file.path == 'notes.txt').index == '?'


def test_change_row_has_direct_stage_control(app, qtbot, tmp_path):
    from PyQt6.QtWidgets import QToolButton
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('notes')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    item = panel.tree.topLevelItem(2).child(0)
    buttons = panel.tree.itemWidget(item, 1).findChildren(QToolButton)
    assert len(buttons) == 2
    buttons[1].click()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert next(file for file in service.status().files if file.path == 'notes.txt').index == 'A'


def test_rendered_review_is_temporary_tab_and_keeps_document_state(app, qtbot, tmp_path):
    from proteus.services.git_document import snapshot
    from proteus.application.state.manager import StateManager
    from proteus.views.components.git_document_review import GitRenderedReview
    panel, service = open_repository(app, qtbot, tmp_path)
    from proteus.application.resources.plugins import Plugins
    app._controller._render_service.add_functions_to_namespace(Plugins().get_xslt_functions())
    obj = next(obj for obj in app._controller.get_objects() if obj.get_document() is not None)
    path = next(path for path in (service.directory / 'objects').rglob('*.xml') if snapshot(path.read_text(encoding='utf-8')).oid == str(obj.id))
    from proteus.services.git_service import GitFile
    file = GitFile(path.relative_to(service.directory).as_posix(), ' ', 'M')
    source = path.read_text(encoding='utf-8')
    root = service.document_revision('proteus.xml', 'HEAD')
    container = app.project_container.views_container
    from copy import deepcopy
    new_root = deepcopy(root)
    title = new_root.xpath('descendant-or-self::object[@id=$oid]/properties/*[@name="text"]', oid=str(obj.id))[0]
    title.text = 'Rendered comparison changed title'
    count = container.count()
    state = StateManager()
    previous = (state.current_document, state.get_current_view())
    panel.present_review(file, False, ('diff', snapshot(source), snapshot(source), (root, new_root)))
    review = container.currentWidget()
    assert isinstance(review, GitRenderedReview)
    assert container.count() == count + 1
    assert (state.current_document, state.get_current_view()) == previous
    assert len(review.browsers) == 2
    temporary_html = Path(review._html_directory.path())
    assert (temporary_html / '0.html').is_file()
    results = []
    qtbot.wait(1200)
    review.browsers[0].page().runJavaScript('document.body.innerText', results.append)
    qtbot.waitUntil(lambda: bool(results), timeout=10000)
    assert results[0].strip()
    highlights = []
    review.browsers[1].page().runJavaScript('document.querySelectorAll("mark").length', highlights.append)
    qtbot.waitUntil(lambda: bool(highlights), timeout=10000)
    assert highlights[0] > 0, (str(obj.id), review._rendered_text)
    assert review.browsers[0].url().isLocalFile()
    assert review.browsers[0].y() < 55
    assert review.browsers[0].height() > review.height() * .7
    review.grab().save(str(tmp_path / 'rendered-review.png'))
    panel.present_review(file, False, ('diff', snapshot(source), snapshot(source), (root, new_root)))
    assert container.count() == count + 1
    qtbot.waitUntil(lambda: not temporary_html.exists(), timeout=5000)
    container.close_tab(container.currentIndex())
    assert container.count() == count
    assert state.get_current_view() == previous[1]


def test_branch_picker_selection_uses_theme_pair(qapp, qtbot, theme_state, tmp_path):
    from PyQt6.QtGui import QPalette
    from proteus.application.resources.themes import Themes
    from proteus.views.components.git_branches import GitBranchDialog
    for theme_name in ('light', 'dark'):
        Themes().select_theme(theme_name)
        dialog = GitBranchDialog([], 'develop')
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.wait(30)
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette = dialog.list.palette()
            assert palette.color(group, QPalette.ColorRole.HighlightedText) == Themes().color('selection_text')
            assert palette.color(group, QPalette.ColorRole.Highlight) == Themes().color('selection_bg')
        dialog.grab().save(str(tmp_path / (theme_name + '-branches.png')))
        dialog.close()


def test_remotes_actions_use_selected_remote_and_prefill_url(qapp, qtbot, tmp_path):
    from proteus.views.components.git_remotes import GitRemotesDialog
    dialog = GitRemotesDialog([('origin', 'https://example.invalid/repo.git')])
    qtbot.addWidget(dialog)
    dialog.show()
    assert not dialog.edit.isEnabled() and not dialog.remove.isEnabled()
    dialog.list.setCurrentItem(dialog.list.topLevelItem(0))
    dialog.edit.click()
    assert dialog.name.text() == 'origin' and dialog.name.isReadOnly()
    assert dialog.url.text() == 'https://example.invalid/repo.git'
    assert not dialog.save.isEnabled()
    dialog.url.setText('https://example.invalid/new.git')
    dialog.grab().save(str(tmp_path / 'remotes.png'))
    dialog.save.click()
    assert dialog.command == ['remote', 'set-url', '--', 'origin', 'https://example.invalid/new.git']
    empty = GitRemotesDialog([])
    qtbot.addWidget(empty)
    empty.add.click()
    empty.name.setText('invalid..name')
    empty.url.setText('https://example.invalid/repo.git')
    assert not empty.save.isEnabled()
    empty.cancel.click()
    assert empty.form.isHidden() and empty.command is None
    empty.add.click()
    empty.name.setText('origin')
    assert not empty.save.isEnabled()
    empty.url.setText('https://example.invalid/repo.git')
    empty.save.click()
    assert empty.command == ['remote', 'add', '--', 'origin', 'https://example.invalid/repo.git']


def test_commit_without_stage_asks_before_staging(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('commit me')
    panel.message.setPlainText('Smart commit')
    prompts = []
    monkeypatch.setattr(panel, 'confirm', lambda message: prompts.append(message) or False)
    panel.commit()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert len(prompts) == 1
    assert service.status().files[0].index == '?'
    monkeypatch.setattr(panel, 'confirm', lambda _: True)
    panel.commit()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert service.run('log', '-1', '--format=%s').strip() == 'Smart commit'
    assert not service.status().files


def test_pull_pending_cancel_and_stash_choices(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('keep local')
    monkeypatch.setattr(panel, 'pick', lambda *_: 'Fast-forward')
    choices = []
    monkeypatch.setattr(panel, 'pending_choice', lambda key, options: choices.append(key) or None)
    panel.pull()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert choices == ['pull_pending']
    assert service.run('stash', 'list') == ''
    called = []
    monkeypatch.setattr(GitService, 'pull_with_stash', lambda self, flag, retained: called.append(flag) or '')
    monkeypatch.setattr(panel, 'pending_choice', lambda *_: 'stash')
    panel.pull()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert called == ['--ff-only']


def test_push_up_to_date_explains_uncommitted_changes(app, qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    panel, service = open_repository(app, qtbot, tmp_path)
    remote = tmp_path / 'remote.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    service.run('remote', 'add', 'origin', str(remote))
    service.publish('origin')
    (service.directory / 'notes.txt').write_text('not committed')
    messages = []
    monkeypatch.setattr(QMessageBox, 'information', lambda parent, title, message: messages.append(message))
    panel.push()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    from proteus.views.components.git_panel import text
    assert messages == [text('push_nothing') + '\n\n' + text('push_uncommitted')]


def test_long_error_does_not_expand_git_dock(app, qtbot, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    panel, service = open_repository(app, qtbot, tmp_path)
    panel.reveal()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    qtbot.wait(50)
    before = panel.width()
    monkeypatch.setattr(QMessageBox, 'warning', lambda *_: None)
    def failure():
        raise RuntimeError('A very long error: ' + 'C:/long/path/file.xml ' * 100)
    panel.job(failure, changes_disk=True)
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    qtbot.wait(100)
    assert panel.width() <= before + 2, (panel.minimumSizeHint().width(), panel.widget().minimumSizeHint().width(), panel.feedback.minimumSizeHint().width())


def test_remote_branch_name_collision_can_create_another_local_name(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    remote = tmp_path / 'remote.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    service.run('remote', 'add', 'origin', str(remote))
    service.publish('origin')
    service.run('branch', '--unset-upstream')
    service.run('config', 'branch.autoSetupMerge', 'false')
    original = service.run('rev-parse', 'refs/heads/develop').strip()
    references = service.references()
    reference = next(ref for ref in references if ref.name == 'origin/develop')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    monkeypatch.setattr(panel, 'pending_choice', lambda *_: 'new')
    monkeypatch.setattr(panel, 'ask', lambda *_: 'remote-develop')
    panel._branch_choice(service, references, ('reference', reference))
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert service.status().branch == 'remote-develop'
    assert service.status().upstream == 'origin/develop'
    assert service.run('rev-parse', 'refs/heads/develop').strip() == original


def test_stage_unstage_and_stash_actions_follow_actual_changes(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    for name in ('stage_all', 'unstage_all', 'stash', 'stage_hunk'):
        assert not panel.actions[name].isEnabled()
    (service.directory / 'notes.txt').write_text('new change')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.actions['stage_all'].isEnabled()
    assert not panel.actions['unstage_all'].isEnabled()
    assert panel.actions['stash'].isEnabled()
    from PyQt6.QtWidgets import QWidget, QPushButton
    review = QWidget()
    review.git_review_key = ('notes.txt', False)
    review.stage = QPushButton(review)
    app.project_container.views_container.addTab(review, 'Test snapshot')
    panel._update_actions()
    assert review.stage.isEnabled()
    panel.stage_all()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.actions['stage_all'].isEnabled()
    assert not review.stage.isEnabled()
    assert panel.actions['unstage_all'].isEnabled()
    assert panel.actions['stash'].isEnabled()
    panel.unstage_all()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.actions['stage_all'].isEnabled()
    assert not panel.actions['unstage_all'].isEnabled()
    assert not panel.actions['apply_stash'].isEnabled()
    panel.stash()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.actions['apply_stash'].isEnabled()
    assert not panel.actions['stash'].isEnabled()
    monkeypatch.setattr(panel, 'pick', lambda key, options: options[0])
    monkeypatch.setattr(panel, 'show_output', lambda *_: None)
    panel.apply_stash()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert (service.directory / 'notes.txt').read_text() == 'new change'
    assert not panel.actions['apply_stash'].isEnabled()


def test_publish_action_follows_current_branch_upstream(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    assert not panel.actions['publish_branch'].isEnabled()
    remote = tmp_path / 'remote.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    service.run('remote', 'add', 'origin', str(remote))
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.actions['publish_branch'].isEnabled()
    service.publish('origin')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not panel.actions['publish_branch'].isEnabled()
    service.switch('unpublished', create=True)
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert panel.actions['publish_branch'].isEnabled()


def test_branch_delete_uses_local_picker_and_inline_result(app, qtbot, tmp_path, monkeypatch):
    from proteus.views.components.git_branches import GitBranchDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('branch', 'remove-me')
    def choose(dialog):
        assert all(ref.kind == 'local' and ref.name != 'develop' for ref in dialog.references)
        dialog.choice = ('reference', next(ref for ref in dialog.references if ref.name == 'remove-me'))
        return 1
    monkeypatch.setattr(GitBranchDialog, 'exec', choose)
    monkeypatch.setattr(panel, 'confirm', lambda *_: True)
    monkeypatch.setattr(panel, 'show_output', lambda *_: (_ for _ in ()).throw(AssertionError('Unexpected result dialog')))
    panel.delete_branch()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert not service.run('show-ref', '--verify', 'refs/heads/remove-me', check=False).strip()
    assert panel.feedback.text()


def test_merge_uses_reference_picker_and_preserves_valid_model(app, qtbot, tmp_path, monkeypatch):
    from proteus.views.components.git_branches import GitBranchDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    service.switch('feature', create=True)
    (service.directory / 'notes.txt').write_text('merge this')
    service.stage(['notes.txt'])
    service.commit('Feature')
    service.switch('develop')
    def choose(dialog):
        dialog.choice = ('reference', next(ref for ref in dialog.references if ref.name == 'feature'))
        return 1
    monkeypatch.setattr(GitBranchDialog, 'exec', choose)
    monkeypatch.setattr(panel, 'confirm', lambda *_: True)
    panel.integrate('merge')
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    assert (service.directory / 'notes.txt').read_text() == 'merge this'
    assert not panel.blocked


def test_read_callback_is_discarded_after_switching_projects(app, qtbot, tmp_path):
    from threading import Event
    panel, service = open_repository(app, qtbot, tmp_path)
    gate = Event()
    callbacks = []
    def work():
        gate.wait(5)
        return 'old project result'
    panel.job(work, callbacks.append)
    other = tmp_path / 'other-project'
    shutil.copytree(PROTEUS_SAMPLE_PROJECTS_PATH / 'example_project', other)
    app._controller.load_project(str(other))
    gate.set()
    qtbot.waitUntil(lambda: not panel.busy and panel._detected, timeout=15000)
    assert not callbacks
    assert panel.directory == other
    assert panel.status is None


def test_worktrees_dialog_displays_paths_branches_and_state(app, qtbot, tmp_path):
    from proteus.services.git_service import GitWorktree
    from proteus.views.components.git_worktrees import GitWorktreesDialog, text
    entries = [GitWorktree(str(tmp_path), 'develop', 'a' * 40),
               GitWorktree(str(tmp_path / 'linked folder'), 'feature', 'b' * 40, locked='Keep this worktree')]
    dialog = GitWorktreesDialog(entries, tmp_path, app)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.table.topLevelItemCount() == 2
    assert dialog.table.topLevelItem(0).text(2) == text('worktree_current')
    assert dialog.table.topLevelItem(1).text(1) == 'feature'
    assert dialog.table.topLevelItem(1).text(2) == text('worktree_locked')
    assert dialog.table.topLevelItem(1).toolTip(2) == 'Keep this worktree'
    dialog.grab().save(str(tmp_path / 'worktrees.png'))
    dialog.create.click()
    assert dialog.action == 'create'


def test_no_remote_and_detached_head_disable_inapplicable_menu_actions(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    assert not panel.actions['fetch'].isEnabled()
    assert not panel.actions['pull'].isEnabled()
    assert not panel.actions['ignore'].isEnabled()
    assert not panel.submenus['conflicts'].menuAction().isVisible()
    service.detach('HEAD')
    panel.refresh()
    qtbot.waitUntil(lambda: not panel.busy, timeout=15000)
    for key in ('push', 'publish_branch', 'rename_branch', 'delete_branch'):
        assert not panel.actions[key].isEnabled()
