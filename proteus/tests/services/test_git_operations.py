"""Real Git operations in isolated repositories, with no external account access."""
import os
import subprocess
from pathlib import Path

import pytest

from proteus.services.git_service import GitError, GitService
from proteus.tests.services.test_git_service import repo, seed


@pytest.fixture(autouse=True)
def isolated_git_config(monkeypatch):
    # Tests must not execute user-wide hooks or inherit signing/merge policies.
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)


def commit_file(service, name, content, message):
    path = service.directory / name
    path.write_text(content, encoding='utf-8')
    service.stage([name])
    service.commit(message)
    return service.run('rev-parse', 'HEAD').strip()


@pytest.fixture
def network(tmp_path):
    remote = tmp_path / 'origin.git'
    local = tmp_path / 'local'
    remote.mkdir()
    local.mkdir()
    GitService(remote).run('init', '--bare')
    service = GitService(local)
    service.run('init', '-b', 'develop')
    service.run('config', 'user.name', 'Test')
    service.run('config', 'user.email', 'test@example.invalid')
    seed(service)
    service.run('remote', 'add', 'origin', str(remote))
    service.publish('origin')
    GitService(tmp_path).run('clone', '--branch', 'develop', '--', str(remote), str(tmp_path / 'peer'))
    peer = GitService(tmp_path / 'peer')
    peer.run('config', 'user.name', 'Peer')
    peer.run('config', 'user.email', 'peer@example.invalid')
    return service, peer, GitService(remote)


@pytest.mark.parametrize('flag', ['--ff-only', '--no-rebase', '--rebase'])
def test_pull_integrates_remote_changes_with_selected_strategy(network, flag):
    local, peer, remote = network
    remote_oid = commit_file(peer, 'remote.txt', 'from remote', 'Remote work')
    peer.run('push')
    if flag != '--ff-only':
        commit_file(local, 'local.txt', 'keep local work', 'Local work')
    local.run('pull', flag)
    assert (local.directory / 'remote.txt').read_text() == 'from remote'
    if flag != '--ff-only':
        assert (local.directory / 'local.txt').read_text() == 'keep local work'
    assert local.run('merge-base', '--is-ancestor', remote_oid, 'HEAD') == ''
    assert not local.status().files


def test_non_fast_forward_push_leaves_both_histories_intact(network):
    local, peer, remote = network
    remote_oid = commit_file(peer, 'remote.txt', 'remote', 'Remote ahead')
    peer.run('push')
    local_oid = commit_file(local, 'local.txt', 'local', 'Local ahead')
    with pytest.raises(GitError):
        local.run('push', '--porcelain')
    assert local.run('rev-parse', 'HEAD').strip() == local_oid
    assert remote.run('rev-parse', 'refs/heads/develop').strip() == remote_oid
    assert (local.directory / 'local.txt').read_text() == 'local'


def test_pull_stash_keeps_recoverable_changes_when_restoration_conflicts(network):
    local, peer, remote = network
    (local.directory / 'document.xml').write_text('<local/>')
    commit_file(peer, 'document.xml', '<remote/>', 'Remote document')
    peer.run('push')
    with pytest.raises(GitError, match='retained'):
        local.pull_with_stash('--ff-only', 'stash retained')
    assert local.status().has_stash
    assert any(file.conflicted for file in local.status().files)
    assert '<local/>' in local.run('show', 'stash@{0}:document.xml')
    assert '<remote/>' in local.run('show', 'HEAD:document.xml')


def test_pull_stash_preserves_preexisting_stashes(network):
    local, peer, remote = network
    (local.directory / 'old.txt').write_text('older stash')
    local.run('stash', 'push', '--include-untracked', '-m', 'Existing stash')
    old_oid = local.run('rev-parse', 'refs/stash').strip()
    (local.directory / 'new.txt').write_text('new work')
    commit_file(peer, 'remote.txt', 'new remote work', 'Remote work')
    peer.run('push')
    local.pull_with_stash('--ff-only', 'stash retained')
    assert local.run('rev-parse', 'refs/stash').strip() == old_oid
    assert (local.directory / 'new.txt').read_text() == 'new work'
    assert not (local.directory / 'old.txt').exists()
    assert (local.directory / 'remote.txt').read_text() == 'new remote work'


@pytest.mark.parametrize('operation', ['merge', 'rebase', 'cherry-pick', 'revert'])
@pytest.mark.parametrize('finish', ['continue', 'abort'])
def test_conflicting_operations_can_continue_or_abort_without_losing_history(repo, operation, finish):
    seed(repo)
    commit_file(repo, 'notes.txt', 'base\n', 'Base notes')
    repo.switch('feature', create=True)
    feature_oid = commit_file(repo, 'notes.txt', 'feature\n', 'Feature notes')
    repo.switch('develop')
    original = commit_file(repo, 'notes.txt', 'current\n', 'Current notes')
    target = 'feature' if operation in ('merge', 'rebase') else feature_oid
    args = [operation, '--no-edit', target] if operation != 'rebase' else [operation, target]
    with pytest.raises(GitError):
        repo.run(*args)
    assert repo.status().operation == operation
    assert any(file.conflicted for file in repo.status().files)
    if finish == 'abort':
        repo.run(operation, '--abort')
        assert repo.run('rev-parse', 'HEAD').strip() == original
        assert (repo.directory / 'notes.txt').read_text() == 'current\n'
    else:
        (repo.directory / 'notes.txt').write_text('resolved\n')
        repo.stage(['notes.txt'])
        repo.run('commit', '--no-edit') if operation == 'merge' else repo.run(operation, '--continue')
        assert (repo.directory / 'notes.txt').read_text() == 'resolved\n'
    assert not repo.status().operation
    assert not repo.status().files


def test_revert_and_cherry_pick_apply_selected_commit_only(repo):
    seed(repo)
    repo.switch('feature', create=True)
    selected = commit_file(repo, 'selected.txt', 'selected', 'Selected change')
    commit_file(repo, 'later.txt', 'later', 'Later change')
    repo.switch('develop')
    repo.run('cherry-pick', '--no-edit', selected)
    assert (repo.directory / 'selected.txt').read_text() == 'selected'
    assert not (repo.directory / 'later.txt').exists()
    repo.run('revert', '--no-edit', 'HEAD')
    assert not (repo.directory / 'selected.txt').exists()
    assert not repo.status().files


def test_rejected_commit_hook_preserves_index_and_head(repo):
    seed(repo)
    original = repo.run('rev-parse', 'HEAD').strip()
    (repo.directory / 'notes.txt').write_text('keep staged')
    repo.stage(['notes.txt'])
    hook = repo.directory / '.git' / 'hooks' / 'pre-commit'
    hook.write_text('#!/bin/sh\necho "REJECTED BY TEST HOOK" >&2\nexit 1\n', encoding='utf-8', newline='\n')
    hook.chmod(0o755)
    with pytest.raises(GitError, match='REJECTED BY TEST HOOK'):
        repo.commit('Must fail')
    assert repo.run('rev-parse', 'HEAD').strip() == original
    assert repo.run('show', ':notes.txt').strip() == 'keep staged'


def test_git_timeout_is_reported_without_shell_execution(repo, monkeypatch):
    def timeout(*args, **kwargs):
        assert not kwargs.get('shell', False)
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
    monkeypatch.setattr(subprocess, 'run', timeout)
    with pytest.raises(GitError, match='timed out'):
        repo.run('status')


def test_staging_stale_hunk_does_not_overwrite_newer_index(repo):
    path = repo.directory / 'notes.txt'
    path.write_text('base\n')
    repo.stage(['notes.txt'])
    repo.commit('Base')
    path.write_text('reviewed\n')
    patch = repo.hunks(repo.status().files[0])[0]
    path.write_text('newer\n')
    repo.stage(['notes.txt'])
    with pytest.raises(GitError):
        repo.stage_hunk(patch)
    assert repo.run('show', ':notes.txt').strip() == 'newer'
    assert path.read_text() == 'newer\n'


def test_binary_diff_does_not_decode_or_execute_file_content(repo):
    path = repo.directory / 'binary.bin'
    path.write_bytes(b'\x00\xff\xfe<not text>')
    assert repo.diff(repo.status().files[0]) == 'Binary file.'
    repo.stage(['binary.bin'])
    repo.commit('Binary')
    path.write_bytes(b'\x00\xffchanged')
    assert 'Binary files' in repo.diff(repo.status().files[0])


def test_revision_batch_handles_unicode_byte_lengths(repo):
    (repo.directory / 'objects').mkdir()
    (repo.directory / 'proteus.xml').write_text('<project id="p"><properties/><documents><document id="doc"/></documents></project>', encoding='utf-8')
    source = '<object id="doc"><properties><stringProperty name=":Proteus-name">Introducción 😀</stringProperty></properties><children/></object>'
    (repo.directory / 'objects' / 'doc.xml').write_text(source, encoding='utf-8')
    repo.stage(['proteus.xml', 'objects/doc.xml'])
    repo.commit('Unicode object')
    root = repo.document_revision('proteus.xml', 'HEAD')
    assert root.find('./documents/object/properties/stringProperty').text == 'Introducción 😀'
