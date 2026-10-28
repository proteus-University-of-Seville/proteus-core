"""Exercise Git UI flows against real temporary repositories.

Only user input, browser launching and GitHub CLI are simulated. Git mutations,
files, project reloads, indexes and histories are real.
"""
import configparser
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox, QPlainTextEdit, QPushButton, QComboBox

from proteus.application.configuration.config import Config
from proteus.services.git_service import GitService, GitError
from proteus.tests import PROTEUS_SAMPLE_PROJECTS_PATH
from proteus.tests.end2end.fixtures import app
from proteus.tests.end2end.test_git_controls import open_repository
from proteus.tests.services.test_git_operations import isolated_git_config, commit_file
from proteus.views.components.git_panel import text


@pytest.fixture(autouse=True)
def messages(monkeypatch):
    collected = {'warning': [], 'information': []}
    for kind in collected:
        monkeypatch.setattr(QMessageBox, kind, lambda parent, title, message, kind=kind: collected[kind].append(str(message)))
    return collected


def wait_idle(panel, qtbot):
    qtbot.waitUntil(lambda: not panel.busy, timeout=20000)


def refresh(panel, qtbot):
    panel.refresh()
    wait_idle(panel, qtbot)


def select_path(panel, path, staged=False):
    panel.tree.clearSelection()
    for i in range(panel.tree.topLevelItemCount()):
        group = panel.tree.topLevelItem(i)
        for j in range(group.childCount()):
            item = group.child(j)
            file, prepared = item.data(0, Qt.ItemDataRole.UserRole)
            if file.path == path and prepared == staged:
                item.setSelected(True)
                return item
    raise AssertionError('Change not found: ' + path)


def begin_conflict(panel, service, qtbot, operation, name='conflict.txt'):
    commit_file(service, name, '<value>base</value>\n', 'Base conflict')
    service.switch('feature', create=True)
    feature = commit_file(service, name, '<value>feature</value>\n', 'Feature conflict')
    service.switch('develop')
    original = commit_file(service, name, '<value>current</value>\n', 'Current conflict')
    refresh(panel, qtbot)
    target = 'feature' if operation in ('merge', 'rebase') else feature
    args = [operation, '--no-edit', target] if operation != 'rebase' else [operation, target]
    panel.command(args, changes_disk=True, require_clean=True)
    wait_idle(panel, qtbot)
    return original


@pytest.mark.parametrize('operation', ['merge', 'rebase', 'cherry-pick', 'revert'])
@pytest.mark.parametrize('finish', ['continue', 'abort'])
def test_conflict_controls_complete_or_abort_real_operation(app, qtbot, tmp_path, monkeypatch, operation, finish):
    panel, service = open_repository(app, qtbot, tmp_path)
    monkeypatch.setattr(panel, 'confirm', lambda *_: True)
    original = begin_conflict(panel, service, qtbot, operation)
    assert panel.blocked
    assert panel.status.operation == operation
    assert not panel.actions['continue'].isEnabled()
    if finish == 'abort':
        monkeypatch.setattr(panel, 'confirm', lambda *_: False)
        panel.abort_operation()
        assert service.status().operation == operation
        monkeypatch.setattr(panel, 'confirm', lambda *_: True)
        panel.abort_operation()
        wait_idle(panel, qtbot)
        assert service.run('rev-parse', 'HEAD').strip() == original
        assert (service.directory / 'conflict.txt').read_text() == '<value>current</value>\n'
    else:
        (service.directory / 'conflict.txt').write_text('resolved\n')
        service.stage(['conflict.txt'])
        refresh(panel, qtbot)
        assert panel.actions['continue'].isEnabled()
        panel.continue_operation()
        wait_idle(panel, qtbot)
        assert (service.directory / 'conflict.txt').read_text() == 'resolved\n'
    assert not panel.status.operation
    assert not panel.blocked
    assert app.project_container.isEnabled()


@pytest.mark.parametrize('operation', ['revert', 'cherry-pick'])
@pytest.mark.parametrize('accepted', [True, False])
def test_commit_actions_use_selected_commit_and_honour_cancel(app, qtbot, tmp_path, monkeypatch, operation, accepted):
    panel, service = open_repository(app, qtbot, tmp_path)
    service.switch('feature', create=True)
    selected = commit_file(service, 'selected.txt', 'selected', 'Selected feature')
    commit_file(service, 'later.txt', 'not selected', 'Later feature')
    service.switch('develop')
    if operation == 'revert':
        service.run('cherry-pick', '--no-edit', selected)
        selected = service.run('rev-parse', 'HEAD').strip()
    refresh(panel, qtbot)
    before = service.run('rev-parse', 'HEAD').strip()
    monkeypatch.setattr(panel, 'ask', lambda *_: selected)
    monkeypatch.setattr(panel, 'confirm', lambda *_: accepted)
    panel.commit_action(operation)
    wait_idle(panel, qtbot)
    if not accepted:
        assert service.run('rev-parse', 'HEAD').strip() == before
    elif operation == 'revert':
        assert not (service.directory / 'selected.txt').exists()
    else:
        assert (service.directory / 'selected.txt').read_text() == 'selected'
    assert not (service.directory / 'later.txt').exists()
    assert not panel.blocked


@pytest.mark.parametrize('answer', ['name-cancel', 'email-cancel', 'save'])
def test_identity_configuration_is_local_and_cancel_is_non_mutating(app, qtbot, tmp_path, monkeypatch, answer):
    panel, service = open_repository(app, qtbot, tmp_path)
    original = (service.run('config', '--local', 'user.name'), service.run('config', '--local', 'user.email'))
    values = {'user_name': None if answer == 'name-cancel' else 'New Author',
              'user_email': None if answer == 'email-cancel' else 'new@example.invalid'}
    monkeypatch.setattr(panel, 'ask', lambda key: values[key])
    panel.identity()
    wait_idle(panel, qtbot)
    actual = (service.run('config', '--local', 'user.name').strip(), service.run('config', '--local', 'user.email').strip())
    assert actual == (('New Author', 'new@example.invalid') if answer == 'save' else tuple(value.strip() for value in original))


@pytest.mark.parametrize('operation,answer', [('create_branch', 'feature-ui'), ('rename_branch', 'renamed-ui'), ('tag', 'release-ui'), ('tag', 'invalid..tag'), ('create_branch', None)])
def test_branch_and_tag_actions_mutate_only_valid_accepted_input(app, qtbot, tmp_path, monkeypatch, messages, operation, answer):
    panel, service = open_repository(app, qtbot, tmp_path)
    before = service.run('rev-parse', 'HEAD').strip()
    monkeypatch.setattr(panel, 'ask', lambda *_: answer)
    panel.actions[operation].trigger()
    wait_idle(panel, qtbot)
    if operation == 'tag' and answer == 'release-ui':
        assert service.run('rev-parse', 'refs/tags/release-ui').strip() == before
    elif operation == 'tag':
        assert messages['warning']
        assert not service.run('tag', '--list').strip()
    elif answer:
        assert service.status().branch == answer
    else:
        assert service.status().branch == 'develop'
    assert service.run('rev-parse', 'HEAD').strip() == before


@pytest.mark.parametrize('case', ['success', 'cancel-url', 'cancel-folder', 'existing-folder', 'invalid-source'])
def test_clone_ui_uses_local_repository_and_handles_cancel_and_errors(app, qtbot, tmp_path, monkeypatch, messages, case):
    panel, source = open_repository(app, qtbot, tmp_path)
    before = source.run('rev-parse', 'HEAD').strip()
    target = tmp_path / 'clone-target'
    if case == 'existing-folder':
        target.mkdir()
        (target / 'keep.txt').write_text('keep')
    url = None if case == 'cancel-url' else str(tmp_path / 'missing-source') if case == 'invalid-source' else str(source.directory)
    monkeypatch.setattr(panel, 'ask', lambda *_: url)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *_: ('' if case == 'cancel-folder' else str(target), ''))
    panel.clone()
    wait_idle(panel, qtbot)
    if case == 'success':
        qtbot.waitUntil(lambda: panel.status is not None and panel.directory == target and not panel.busy, timeout=20000)
        assert Path(app._controller.get_current_project().path).parent == target
        assert GitService(target).run('rev-parse', 'HEAD').strip() == before
    else:
        assert panel.directory == source.directory
        if case == 'existing-folder':
            assert (target / 'keep.txt').read_text() == 'keep'
        if case in ('existing-folder', 'invalid-source'):
            assert messages['warning']
    assert source.run('rev-parse', 'HEAD').strip() == before


@pytest.mark.parametrize('accepted', [True, False])
def test_initialize_repository_requires_confirmation(app, qtbot, tmp_path, monkeypatch, messages, accepted):
    target = tmp_path / 'new-project'
    shutil.copytree(PROTEUS_SAMPLE_PROJECTS_PATH / 'example_project', target)
    app._controller.load_project(str(target))
    panel = app.git_panel
    qtbot.waitUntil(lambda: panel._detected and not panel.busy, timeout=15000)
    assert panel.status is None
    monkeypatch.setattr(panel, 'confirm', lambda *_: accepted)
    panel.initialize()
    wait_idle(panel, qtbot)
    assert (target / '.git').exists() == accepted
    assert (target / 'proteus.xml').is_file()
    if accepted:
        panel.push()
        wait_idle(panel, qtbot)
        assert messages['information'] == [text('push_first_commit')]


@pytest.mark.parametrize('accepted', [True, False])
def test_discard_restores_index_version_without_touching_staged_content(app, qtbot, tmp_path, monkeypatch, accepted):
    panel, service = open_repository(app, qtbot, tmp_path)
    commit_file(service, 'notes.txt', 'base', 'Base notes')
    (service.directory / 'notes.txt').write_text('staged')
    service.stage(['notes.txt'])
    (service.directory / 'notes.txt').write_text('unstaged')
    refresh(panel, qtbot)
    select_path(panel, 'notes.txt')
    monkeypatch.setattr(panel, 'confirm', lambda *_: accepted)
    panel.discard()
    wait_idle(panel, qtbot)
    assert service.run('show', ':notes.txt').strip() == 'staged'
    assert (service.directory / 'notes.txt').read_text() == ('staged' if accepted else 'unstaged')


def test_discard_never_deletes_untracked_files(app, qtbot, tmp_path, messages):
    panel, service = open_repository(app, qtbot, tmp_path)
    path = service.directory / 'new.txt'
    path.write_text('must survive')
    refresh(panel, qtbot)
    select_path(panel, 'new.txt')
    panel.discard()
    assert path.read_text() == 'must survive'
    assert messages['information']


@pytest.mark.parametrize('accepted', [True, False])
def test_ignore_escapes_file_names_and_honours_cancellation(app, qtbot, tmp_path, monkeypatch, accepted):
    panel, service = open_repository(app, qtbot, tmp_path)
    name = '[draft] file#1.txt'
    path = service.directory / name
    path.write_text('keep file')
    refresh(panel, qtbot)
    select_path(panel, name)
    monkeypatch.setattr(panel, 'confirm', lambda *_: accepted)
    panel.ignore()
    wait_idle(panel, qtbot)
    ignored = name not in {file.path for file in service.status().files}
    assert ignored == accepted
    assert path.read_text() == 'keep file'


def test_hunk_picker_stages_selected_hunk_only(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    source = ''.join(f'line {i}\n' for i in range(40))
    commit_file(service, 'notes.txt', source, 'Multiline')
    changed = source.replace('line 1\n', 'changed first\n').replace('line 35\n', 'changed second\n')
    (service.directory / 'notes.txt').write_text(changed)
    refresh(panel, qtbot)
    select_path(panel, 'notes.txt')
    def accept(dialog):
        dialog.findChild(QComboBox).setCurrentIndex(1)
        return 1
    monkeypatch.setattr(QDialog, 'exec', accept)
    panel.stage_hunk()
    wait_idle(panel, qtbot)
    indexed = service.run('show', ':notes.txt')
    assert 'changed second' in indexed and 'changed first' not in indexed
    assert (service.directory / 'notes.txt').read_text() == changed


def test_create_worktree_keeps_original_checkout_and_creates_new_branch(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    target = tmp_path / 'new-worktree'
    before = service.run('rev-parse', 'HEAD').strip()
    monkeypatch.setattr(panel, 'ask', lambda *_: 'worktree-feature')
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *_: (str(target), ''))
    from proteus.views.components.git_worktrees import GitWorktreesDialog
    def create(dialog):
        assert dialog.table.topLevelItemCount() == 1
        dialog.action = 'create'
        return 1
    monkeypatch.setattr(GitWorktreesDialog, 'exec', create)
    panel.worktrees()
    wait_idle(panel, qtbot)
    try:
        assert GitService(target).status().branch == 'worktree-feature'
        assert (target / 'proteus.xml').is_file()
        assert service.run('rev-parse', 'HEAD').strip() == before
        assert service.status().branch == 'develop'
    finally:
        if target.exists():
            service.run('worktree', 'remove', str(target))


def test_publish_push_fetch_and_pull_ui_against_local_remote(app, qtbot, tmp_path, monkeypatch, messages):
    panel, service = open_repository(app, qtbot, tmp_path)
    panel.push()
    wait_idle(panel, qtbot)
    assert messages['information'] == [text('configure_remote_first')]
    remote = tmp_path / 'origin.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    service.run('remote', 'add', 'origin', str(remote))
    refresh(panel, qtbot)
    monkeypatch.setattr(panel, 'pick', lambda key, options: 'Fast-forward' if key == 'pull_strategy' else 'origin')
    panel.actions['publish_branch'].trigger()
    wait_idle(panel, qtbot)
    assert service.status().upstream == 'origin/develop'
    assert not panel.actions['publish_branch'].isEnabled()
    pushed = commit_file(service, 'local.txt', 'send this', 'Local commit')
    refresh(panel, qtbot)
    assert panel.status.ahead == 1
    panel.actions['push'].trigger()
    wait_idle(panel, qtbot)
    assert GitService(remote).run('rev-parse', 'refs/heads/develop').strip() == pushed
    GitService(tmp_path).run('clone', '--branch', 'develop', '--', str(remote), str(tmp_path / 'peer'))
    peer = GitService(tmp_path / 'peer')
    peer.run('config', 'user.name', 'Peer')
    peer.run('config', 'user.email', 'peer@example.invalid')
    commit_file(peer, 'remote.txt', 'fetch and pull this', 'Remote commit')
    peer.run('push')
    panel.actions['fetch'].trigger()
    wait_idle(panel, qtbot)
    assert panel.status.behind == 1
    assert not (service.directory / 'remote.txt').exists()
    panel.actions['pull'].trigger()
    wait_idle(panel, qtbot)
    assert (service.directory / 'remote.txt').read_text() == 'fetch and pull this'
    assert not panel.status.behind and not panel.blocked


def test_commit_then_pull_rebase_preserves_local_and_remote_work(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    remote = tmp_path / 'origin.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    service.run('remote', 'add', 'origin', str(remote))
    service.publish('origin')
    GitService(tmp_path).run('clone', '--branch', 'develop', '--', str(remote), str(tmp_path / 'peer'))
    peer = GitService(tmp_path / 'peer')
    peer.run('config', 'user.name', 'Peer')
    peer.run('config', 'user.email', 'peer@example.invalid')
    commit_file(peer, 'remote.txt', 'remote work', 'Remote')
    peer.run('push')
    (service.directory / 'local.txt').write_text('uncommitted local work')
    refresh(panel, qtbot)
    panel.message.setPlainText('Commit before pull')
    monkeypatch.setattr(panel, 'pick', lambda *_: 'Rebase')
    monkeypatch.setattr(panel, 'pending_choice', lambda *_: 'commit')
    monkeypatch.setattr(panel, 'confirm', lambda *_: True)
    panel.pull()
    wait_idle(panel, qtbot)
    assert (service.directory / 'local.txt').read_text() == 'uncommitted local work'
    assert (service.directory / 'remote.txt').read_text() == 'remote work'
    assert service.run('log', '-1', '--format=%s').strip() == 'Commit before pull'
    assert not panel.status.files and not panel.blocked
    assert not panel.message.toPlainText()


@pytest.mark.parametrize('choice', ['local', 'create', 'create-from-tag', 'detach-tag', 'cancel'])
def test_branch_selector_routes_choices_and_cancellation_to_real_git(app, qtbot, tmp_path, monkeypatch, choice):
    from proteus.views.components.git_branches import GitBranchDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('branch', 'feature')
    service.run('tag', 'v1')
    before = service.run('rev-parse', 'HEAD').strip()
    def choose(dialog):
        if choice == 'cancel':
            return 0
        if dialog.mode == 'switch':
            if choice == 'local':
                dialog.choice = ('reference', next(ref for ref in dialog.references if ref.name == 'feature'))
            else:
                dialog.choice = ({'create': 'create', 'create-from-tag': 'create_from', 'detach-tag': 'detach'}[choice], None)
        else:
            dialog.choice = ('reference', next(ref for ref in dialog.references if ref.name == 'v1'))
        return 1
    monkeypatch.setattr(GitBranchDialog, 'exec', choose)
    monkeypatch.setattr(panel, 'ask', lambda *_: 'created-ui')
    panel.actions['branches'].trigger()
    wait_idle(panel, qtbot)
    expected = {'local': 'feature', 'create': 'created-ui', 'create-from-tag': 'created-ui', 'cancel': 'develop'}
    if choice == 'detach-tag':
        assert panel.status.branch.startswith('HEAD ')
        assert not panel.actions['publish_branch'].isEnabled()
    else:
        assert panel.status.branch == expected[choice]
    assert service.run('rev-parse', 'HEAD').strip() == before
    assert not panel.blocked


def test_copy_repository_path_and_panel_toggle_preserve_context(app, qtbot, tmp_path):
    from PyQt6.QtGui import QGuiApplication
    panel, service = open_repository(app, qtbot, tmp_path)
    panel.reveal()
    wait_idle(panel, qtbot)
    before = panel.status.branch
    original_clipboard = QGuiApplication.clipboard().text()
    try:
        panel.copy_path.click()
        assert Path(QGuiApplication.clipboard().text()) == service.directory
    finally:
        QGuiApplication.clipboard().setText(original_clipboard)
    toggle = panel.toggleViewAction()
    toggle.trigger()
    assert not panel.isVisible()
    toggle.trigger()
    assert panel.isVisible() and panel.status.branch == before


def test_cancel_saving_pending_edits_does_not_stage_or_clear_commit_draft(app, qtbot, tmp_path, monkeypatch):
    panel, service = open_repository(app, qtbot, tmp_path)
    (service.directory / 'notes.txt').write_text('not staged')
    panel.message.setPlainText('Keep draft')
    monkeypatch.setattr(panel.controller, 'check_unsaved_changes', lambda: True)
    monkeypatch.setattr(panel, 'confirm', lambda *_: False)
    panel.commit()
    assert not panel.busy
    assert service.status().files[0].index == '?'
    assert panel.message.toPlainText() == 'Keep draft'



def test_stage_mixed_selection_preserves_previously_staged_version(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    commit_file(service, 'partial.txt', 'base', 'Base partial')
    (service.directory / 'partial.txt').write_text('reviewed')
    service.stage(['partial.txt'])
    (service.directory / 'partial.txt').write_text('later unreviewed edit')
    (service.directory / 'new.txt').write_text('include this')
    refresh(panel, qtbot)
    panel.tree.clearSelection()
    for group_index in range(panel.tree.topLevelItemCount()):
        group = panel.tree.topLevelItem(group_index)
        for index in range(group.childCount()):
            item = group.child(index)
            file, staged = item.data(0, Qt.ItemDataRole.UserRole)
            item.setSelected((file.path, staged) in {('partial.txt', True), ('new.txt', False)})
    panel.stage()
    wait_idle(panel, qtbot)
    assert service.run('show', ':partial.txt') == 'reviewed'
    assert service.run('show', ':new.txt') == 'include this'
    assert (service.directory / 'partial.txt').read_text() == 'later unreviewed edit'


@pytest.mark.parametrize('url', [
    'https://secret@host:invalid/team/repo.git',
    'https://secret@[broken/team/repo.git',
])
def test_invalid_remote_url_does_not_break_repository_status(app, qtbot, tmp_path, url):
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('remote', 'add', 'origin', url)
    refresh(panel, qtbot)
    assert panel.remote_label.text() == text('invalid_remote_url')
    assert panel.remote_label.toolTip() == text('invalid_remote_url')
    assert 'secret' not in panel.feedback.text()
    assert panel.branch_button.isEnabled()



def test_unborn_branch_disables_history_and_stash_but_allows_initial_commit(app, qtbot, tmp_path):
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('checkout', '--orphan', 'new-history')
    refresh(panel, qtbot)
    assert not panel.status.has_commits
    assert panel.status.files
    assert not panel.actions['history'].isEnabled()
    assert not panel.actions['stash'].isEnabled()
    assert panel.commit_button.isEnabled()
