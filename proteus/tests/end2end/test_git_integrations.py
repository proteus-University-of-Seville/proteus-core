"""Configuration, conflict editor and optional GitHub integration safeguards."""
import configparser
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDialog, QFileDialog, QPlainTextEdit, QPushButton

from proteus.services.git_service import GitService, GitError
from proteus.tests.end2end.fixtures import app
from proteus.tests.end2end.test_git_controls import open_repository
from proteus.tests.end2end.test_git_actions import messages, refresh, wait_idle, select_path, begin_conflict
from proteus.tests.services.test_git_operations import isolated_git_config
from proteus.views.components.git_panel import text


@pytest.mark.parametrize('case', ['save', 'delete', 'invalid-then-save', 'external-change', 'cancel'])
def test_conflict_editor_validates_xml_and_preserves_external_changes(app, qtbot, tmp_path, monkeypatch, messages, case):
    panel, service = open_repository(app, qtbot, tmp_path)
    monkeypatch.setattr(panel, 'confirm', lambda *_: True)
    begin_conflict(panel, service, qtbot, 'merge', 'conflict.xml')
    select_path(panel, 'conflict.xml')
    path = service.directory / 'conflict.xml'
    original = path.read_bytes()
    def edit(dialog):
        if case == 'cancel':
            return 0
        editor = dialog.findChildren(QPlainTextEdit)[-1]
        buttons = {button.text(): button for button in dialog.findChildren(QPushButton)}
        if case == 'delete':
            buttons[text('resolve_delete')].click()
        else:
            if case == 'invalid-then-save':
                editor.setPlainText('not valid XML')
                buttons[text('resolve_save')].click()
                assert path.read_bytes() == original
                assert messages['warning']
                assert any(file.conflicted for file in service.status().files)
            editor.setPlainText('<value>resolved</value>')
            if case == 'external-change':
                path.write_text('<value>external edit</value>')
            buttons[text('resolve_save')].click()
        return 1
    monkeypatch.setattr(QDialog, 'exec', edit)
    panel.resolve()
    wait_idle(panel, qtbot)
    if case == 'cancel':
        assert path.read_bytes() == original
        assert any(file.conflicted for file in service.status().files)
    elif case == 'external-change':
        assert path.read_text() == '<value>external edit</value>'
        assert any(file.conflicted for file in service.status().files)
        assert messages['warning']
    else:
        assert not any(file.conflicted for file in service.status().files)
        if case == 'delete':
            assert not path.exists()
        else:
            assert path.read_text() == '<value>resolved</value>'
            assert '<value>resolved</value>' in service.run('show', ':conflict.xml')
        panel.continue_operation()
        wait_idle(panel, qtbot)
        assert not panel.blocked and not panel.status.operation


@pytest.mark.parametrize('case', ['add', 'edit', 'remove', 'cancel-remove', 'cancel-dialog'])
def test_remote_management_actions_update_only_selected_remote(app, qtbot, tmp_path, monkeypatch, case):
    from proteus.views.components.git_remotes import GitRemotesDialog
    panel, service = open_repository(app, qtbot, tmp_path)
    service.run('remote', 'add', 'upstream', 'https://example.invalid/upstream.git')
    if case != 'add':
        service.run('remote', 'add', 'origin', 'https://example.invalid/original.git')
    refresh(panel, qtbot)
    def choose(dialog):
        assert dialog.list.topLevelItemCount() == (1 if case == 'add' else 2)
        if case == 'cancel-dialog':
            return 0
        command = {'add': ['remote', 'add', '--', 'origin', 'https://example.invalid/new.git'],
                   'edit': ['remote', 'set-url', '--', 'origin', 'https://example.invalid/new.git']}.get(case,
                       ['remote', 'remove', '--', 'origin'])
        dialog.command = command
        return 1
    monkeypatch.setattr(GitRemotesDialog, 'exec', choose)
    monkeypatch.setattr(panel, 'confirm', lambda *_: case != 'cancel-remove')
    panel.remotes()
    wait_idle(panel, qtbot)
    assert service.run('remote', 'get-url', 'upstream').strip() == 'https://example.invalid/upstream.git'
    if case == 'remove':
        assert 'origin' not in service.remote_names()
    else:
        expected = 'new' if case in ('add', 'edit') else 'original'
        assert service.run('remote', 'get-url', 'origin').strip() == f'https://example.invalid/{expected}.git'


@pytest.mark.parametrize('case', ['success', 'auth-error', 'timeout', 'existing-origin', 'cancel-name', 'cancel-visibility', 'cancel-confirm'])
def test_github_cli_is_optional_confirmed_and_reports_failures(app, qtbot, tmp_path, monkeypatch, messages, case):
    panel, service = open_repository(app, qtbot, tmp_path)
    if case == 'existing-origin':
        service.run('remote', 'add', 'origin', 'https://example.invalid/existing.git')
    original_head = service.run('rev-parse', 'HEAD').strip()
    original_which = shutil.which
    original_run = subprocess.run
    executable = str(tmp_path / 'fake-gh.exe')
    calls = []
    monkeypatch.setattr(shutil, 'which', lambda name, *args, **kwargs: executable if name == 'gh' else original_which(name, *args, **kwargs))
    def run(args, *positional, **kwargs):
        if args[0] != executable:
            return original_run(args, *positional, **kwargs)
        calls.append((args, kwargs))
        assert not kwargs.get('shell', False)
        if case == 'timeout':
            raise subprocess.TimeoutExpired(args, kwargs['timeout'])
        return SimpleNamespace(returncode=1 if case == 'auth-error' else 0,
                               stdout=b'https://example.invalid/test/repository',
                               stderr=b'Authentication required: gh auth login' if case == 'auth-error' else b'')
    monkeypatch.setattr(subprocess, 'run', run)
    monkeypatch.setattr(panel, 'ask', lambda *_: None if case == 'cancel-name' else 'test/repository')
    monkeypatch.setattr(panel, 'pick', lambda *_: None if case == 'cancel-visibility' else 'private')
    monkeypatch.setattr(panel, 'confirm', lambda *_: case != 'cancel-confirm')
    outputs = []
    monkeypatch.setattr(panel, 'show_output', outputs.append)
    panel.publish_github()
    wait_idle(panel, qtbot)
    if case in ('existing-origin', 'cancel-name', 'cancel-visibility', 'cancel-confirm'):
        assert not calls
    else:
        assert len(calls) == 1
        args, kwargs = calls[0]
        assert args == [executable, 'repo', 'create', 'test/repository', '--private', '--source', str(service.directory), '--remote', 'origin', '--push']
        assert kwargs['cwd'] == service.directory
        assert bool(outputs) == (case == 'success')
    if case in ('auth-error', 'timeout', 'existing-origin'):
        assert messages['warning']
    assert service.run('rev-parse', 'HEAD').strip() == original_head


@pytest.mark.parametrize('case', ['valid', 'invalid', 'cancel'])
def test_git_executable_selection_validates_before_saving(app, qtbot, tmp_path, monkeypatch, case):
    import proteus.views.components.git_panel as module
    panel, service = open_repository(app, qtbot, tmp_path)
    before = panel.git_executable
    saved = []
    settings = SimpleNamespace(config_parser=configparser.ConfigParser(), save=lambda: saved.append(True))
    monkeypatch.setattr(module, 'Config', lambda: SimpleNamespace(app_settings=settings))
    path = shutil.which('git') if case == 'valid' else sys.executable if case == 'invalid' else ''
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *_: (path, ''))
    if case == 'invalid':
        with pytest.raises(GitError):
            panel.set_git_path()
    else:
        panel.set_git_path()
        wait_idle(panel, qtbot)
    if case == 'valid':
        assert saved == [True]
        assert settings.config_parser.get('git', 'executable') == path
        assert panel.git_executable == path
    else:
        assert not saved and panel.git_executable == before


@pytest.mark.parametrize('accepted', [True, False])
def test_repository_trust_is_session_only_and_can_be_cancelled(app, qtbot, tmp_path, monkeypatch, accepted):
    panel, service = open_repository(app, qtbot, tmp_path)
    monkeypatch.setenv('GIT_TEST_ASSUME_DIFFERENT_OWNER', '1')
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *_: str(service.directory))
    monkeypatch.setattr(panel, 'confirm', lambda *_: accepted)
    panel.trust_repository()
    wait_idle(panel, qtbot)
    assert panel.trusted_root == (service.directory if accepted else None)
    with pytest.raises(GitError, match='dubious ownership'):
        GitService(service.directory).status()
    if accepted:
        assert panel.status is not None
