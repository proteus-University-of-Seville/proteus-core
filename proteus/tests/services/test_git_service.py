"""Integration tests use real disposable Git repositories, never user remotes."""
from pathlib import Path
import os
import subprocess

import pytest

from proteus.services.git_service import GitError, GitService


@pytest.fixture
def repo(tmp_path, monkeypatch):
    # The host may trust all repositories or configure hooks/signing globally.
    # Exercise ownership checks and local mutations without inheriting that state.
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    service = GitService(tmp_path)
    service.run('init', '-b', 'develop')
    service.run('config', 'core.autocrlf', 'input')
    service.run('config', 'user.name', 'PROTEUS Test')
    service.run('config', 'user.email', 'test@example.invalid')
    return service


def seed(repo):
    (repo.directory / 'document.xml').write_text('<document/>', encoding='utf-8')
    repo.stage(['document.xml'])
    repo.commit('Initial document')


def test_missing_repository_is_distinct_from_git_failure(tmp_path):
    assert GitService(tmp_path).status() is None
    with pytest.raises(GitError):
        GitService(tmp_path, 'proteus-missing-git-executable')


def test_unborn_branch_stage_unstage_and_commit(repo):
    assert repo.status().branch == 'develop'
    assert not repo.status().has_commits
    assert repo.status().upstream == ''
    path = 'document á with spaces.xml'
    (repo.directory / path).write_text('<document/>', encoding='utf-8')
    assert repo.status().files[0].path == path
    repo.stage([path])
    assert repo.status().files[0].index == 'A'
    repo.unstage([path])
    assert repo.status().files[0].index == '?'
    repo.stage([path])
    repo.commit('First')
    assert repo.status().has_commits
    assert not repo.status().files


def test_diff_distinguishes_index_and_worktree(repo):
    seed(repo)
    path = repo.directory / 'document.xml'
    path.write_text('<document staged="yes"/>', encoding='utf-8')
    repo.stage(['document.xml'])
    path.write_text('<document working="yes"/>', encoding='utf-8')
    file = repo.status().files[0]
    assert file.index == file.worktree == 'M'
    assert '+<document staged="yes"/>' in repo.diff(file, staged=True)
    assert '+<document working="yes"/>' in repo.diff(file)
    repo.unstage([file.path])
    assert repo.status().files[0].index == ' '


def test_rename_and_deleted_files(repo):
    seed(repo)
    repo.run('mv', 'document.xml', 'new name.xml')
    file = repo.status().files[0]
    assert file.original == 'document.xml'
    assert file.path == 'new name.xml'
    repo.commit('Rename')
    (repo.directory / 'new name.xml').unlink()
    repo.stage(['new name.xml'])
    assert repo.status().files[0].index == 'D'


def test_literal_pathspec_does_not_stage_other_files(repo):
    (repo.directory / '[one].xml').write_text('one')
    (repo.directory / 'o.xml').write_text('other')
    repo.stage(['[one].xml'])
    assert {f.path for f in repo.status().files if f.index == 'A'} == {'[one].xml'}


def test_parent_discovery_and_worktree(repo, tmp_path):
    seed(repo)
    child = repo.directory / 'child'
    child.mkdir()
    assert GitService(child).root() == repo.directory
    checkout = tmp_path.parent / (tmp_path.name + '-worktree')
    repo.run('worktree', 'add', '-b', 'other', str(checkout))
    try:
        status = GitService(checkout).status()
        assert status.branch == 'other'
        assert status.root == checkout
        entries = repo.worktrees()
        assert {Path(entry.path).resolve() for entry in entries} == {repo.directory.resolve(), checkout.resolve()}
        assert next(entry for entry in entries if Path(entry.path).resolve() == checkout.resolve()).branch == 'other'
    finally:
        repo.run('worktree', 'remove', str(checkout))


def test_branches_publish_fetch_pull_and_ahead_behind(repo, tmp_path):
    seed(repo)
    bare = tmp_path / 'remote.git'
    bare.mkdir()
    GitService(bare).run('init', '--bare')
    repo.run('remote', 'add', 'origin', str(bare))
    repo.publish('origin')
    assert repo.status().upstream == 'origin/develop'
    repo.switch('git-controls', create=True)
    repo.publish('origin')
    (repo.directory / 'document.xml').write_text('<changed/>')
    repo.stage(['document.xml'])
    repo.commit('Change')
    assert repo.status().ahead == 1
    repo.run('push')
    assert repo.status().ahead == 0
    repo.switch('develop')
    assert '<document/>' == (repo.directory / 'document.xml').read_text()
    assert 'git-controls' in repo.branches()
    repo.run('fetch', '--all', '--prune')
    repo.run('pull', '--ff-only')


def test_merge_conflict_is_detected_and_can_abort(repo):
    seed(repo)
    repo.switch('other', create=True)
    (repo.directory / 'document.xml').write_text('<other/>')
    repo.stage(['document.xml'])
    repo.commit('Other')
    repo.switch('develop')
    (repo.directory / 'document.xml').write_text('<develop/>')
    repo.stage(['document.xml'])
    repo.commit('Develop')
    with pytest.raises(GitError):
        repo.run('merge', '--no-edit', 'other')
    state = repo.status()
    assert state.operation == 'merge'
    assert state.files[0].conflicted
    repo.run('merge', '--abort')
    assert not repo.status().files
    assert not repo.status().operation


def test_hooks_and_invalid_branch_errors_are_propagated(repo):
    seed(repo)
    with pytest.raises(GitError):
        repo.switch('--delete')
    with pytest.raises(GitError):
        repo.commit('')
    with pytest.raises(GitError):
        repo.run('switch', 'missing-branch')


def test_git_environment_cannot_redirect_operations(repo, tmp_path, monkeypatch):
    seed(repo)
    monkeypatch.setenv('GIT_DIR', str(tmp_path / 'missing.git'))
    monkeypatch.setenv('GIT_WORK_TREE', str(tmp_path / 'missing'))
    assert repo.status().root == tmp_path


def test_stage_one_hunk_preserves_other_worktree_changes(repo):
    path = repo.directory / 'document.xml'
    path.write_text(''.join(f'line {i}\n' for i in range(30)), encoding='utf-8')
    repo.stage(['document.xml'])
    repo.commit('Initial multiline')
    content = path.read_text().replace('line 1\n', 'changed 1\n').replace('line 25\n', 'changed 25\n')
    path.write_text(content, encoding='utf-8')
    hunks = repo.hunks(repo.status().files[0])
    assert len(hunks) == 2
    repo.stage_hunk(hunks[0])
    staged = repo.run('show', ':document.xml')
    assert 'changed 1\n' in staged
    assert 'changed 25\n' not in staged
    assert 'changed 25\n' in path.read_text()


def test_select_remote_branch_creates_tracking_branch(repo, tmp_path):
    seed(repo)
    repo.switch('remote-feature', create=True)
    bare = tmp_path / 'remote.git'
    bare.mkdir()
    GitService(bare).run('init', '--bare')
    repo.run('remote', 'add', 'origin', str(bare))
    repo.publish('origin')
    repo.switch('develop')
    repo.run('branch', '-D', 'remote-feature')
    repo.switch('origin/remote-feature')
    assert repo.status().branch == 'remote-feature'
    assert repo.status().upstream == 'origin/remote-feature'


def test_ownership_trust_is_explicit_and_scoped_to_one_repository(repo, monkeypatch):
    monkeypatch.setenv('GIT_TEST_ASSUME_DIFFERENT_OWNER', '1')
    with pytest.raises(GitError, match='dubious ownership'):
        repo.status()
    trusted = GitService(repo.directory, trusted_root=repo.directory)
    assert trusted.status().branch == 'develop'
    with pytest.raises(GitError, match='dubious ownership'):
        GitService(repo.directory).status()


def test_structured_history_handles_unicode_parents_and_pagination(repo):
    assert repo.history() == ()
    seed(repo)
    first = repo.history()[0]
    assert first.subject == 'Initial document'
    assert first.parents == ()
    assert first.author == 'PROTEUS Test'
    assert 'develop' in first.references
    (repo.directory / 'document.xml').write_text('<new/>')
    repo.stage(['document.xml'])
    repo.commit('Unicode \u00e1 | commit')
    commits = repo.history(limit=1)
    assert commits[0].parents == (first.oid,)
    assert commits[0].subject == 'Unicode \u00e1 | commit'
    assert tuple(commit.oid for commit in repo.history(limit=1, skip=1)) == (first.oid,)
    assert '<new/>' in repo.commit_details(commits[0].oid)


def test_history_graph_tracks_both_merge_parents(repo):
    from proteus.views.components.git_history import graph_rows
    seed(repo)
    repo.switch('feature', create=True)
    (repo.directory / 'feature.txt').write_text('feature')
    repo.stage(['feature.txt'])
    repo.commit('Feature')
    repo.switch('develop')
    (repo.directory / 'main.txt').write_text('main')
    repo.stage(['main.txt'])
    repo.commit('Main')
    repo.run('merge', '--no-ff', '--no-edit', 'feature')
    commits = repo.history()
    assert len(commits[0].parents) == 2
    rows = graph_rows(commits)
    assert len(rows[0][3]) == 2
    assert rows[-1][3] == []
    assert all(0 <= lane < row[-1] for row in rows for lane in row[3])


def test_reference_picker_metadata_tags_and_remote_head(repo):
    seed(repo)
    oid = repo.history()[0].oid
    repo.run('tag', '-a', 'v1', '-m', 'Release')
    repo.run('remote', 'add', 'origin', 'https://example.invalid/project.git')
    repo.run('update-ref', 'refs/remotes/origin/develop', oid)
    repo.run('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/develop')
    refs = repo.references()
    assert {(ref.name, ref.kind) for ref in refs} == {('develop', 'local'), ('origin/develop', 'remote'), ('v1', 'tag')}
    assert all(ref.oid == oid for ref in refs)
    assert all(ref.subject == 'Initial document' for ref in refs)
    assert all(ref.author == 'PROTEUS Test' for ref in refs)
    repo.create_branch('from-tag', 'refs/tags/v1')
    assert repo.status().branch == 'from-tag'
    repo.create_branch('from-remote', 'refs/remotes/origin/develop')
    assert repo.status().upstream == 'origin/develop'
    repo.detach('refs/tags/v1')
    assert repo.status().branch.startswith('HEAD ')


def test_document_review_compares_head_index_and_worktree_separately(repo):
    path = repo.directory / 'object.xml'
    path.write_text('<object id="one">original</object>', encoding='utf-8')
    repo.stage(['object.xml'])
    repo.commit('Original')
    path.write_text('<object id="one">prepared</object>', encoding='utf-8')
    repo.stage(['object.xml'])
    path.write_text('<object id="one">working</object>', encoding='utf-8')
    file = repo.status().files[0]
    before, after = repo.change_content(file, staged=True)
    assert 'original' in before and 'prepared' in after
    before, after = repo.change_content(file)
    assert 'prepared' in before and 'working' in after


def test_render_snapshot_keeps_head_index_and_worktree_distinct(repo, monkeypatch):
    folder = repo.directory / 'nested' / 'objects'
    folder.mkdir(parents=True)
    project = folder.parent / 'proteus.xml'
    project.write_text('<project id="p"><properties/><documents><document id="doc"/></documents></project>')
    path = folder / 'doc.xml'
    source = '<object id="doc"><properties><stringProperty name=":Proteus-name">OLD</stringProperty></properties><children/></object>'
    path.write_text(source)
    repo.stage(['nested'])
    repo.commit('Document')
    path.write_text(source.replace('OLD', 'INDEX'))
    repo.stage(['nested'])
    path.write_text(source.replace('OLD', 'WORKTREE'))
    calls = []
    original_run = repo.run
    def tracked_run(*args, **kwargs):
        calls.append(args[0])
        return original_run(*args, **kwargs)
    monkeypatch.setattr(repo, 'run', tracked_run)
    for revision, value in [('HEAD','OLD'), ('index','INDEX'), ('worktree','WORKTREE')]:
        calls.clear()
        root = repo.document_revision('nested/proteus.xml', revision)
        assert root.find('./documents/object/properties/stringProperty').text == value
        assert len(calls) == (0 if revision == 'worktree' else 2)
    assert path.read_text() == source.replace('OLD', 'WORKTREE')


def test_pull_stash_restores_index_worktree_and_untracked(repo, tmp_path):
    seed(repo)
    remote = tmp_path.parent / (tmp_path.name + '-remote.git')
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    repo.run('remote', 'add', 'origin', str(remote))
    repo.publish('origin')
    path = repo.directory / 'document.xml'
    path.write_text('<staged/>')
    repo.stage(['document.xml'])
    path.write_text('<working/>')
    (repo.directory / 'new.txt').write_text('untracked')
    result = repo.pull_with_stash('--ff-only', 'stash retained')
    assert path.read_text() == '<working/>'
    assert repo.run('show', ':document.xml').strip() == '<staged/>'
    assert (repo.directory / 'new.txt').read_text() == 'untracked'
    assert repo.run('stash', 'list') == ''


def test_failed_pull_keeps_recoverable_stash(repo):
    seed(repo)
    (repo.directory / 'notes.txt').write_text('keep me')
    with pytest.raises(GitError, match='stash retained'):
        repo.pull_with_stash('--ff-only', 'stash retained')
    assert 'PROTEUS: changes before pull' in repo.run('stash', 'list')
    repo.run('stash', 'apply', '--index')
    assert (repo.directory / 'notes.txt').read_text() == 'keep me'


def test_remote_selection_reuses_existing_tracking_branch_and_local_commits(repo, tmp_path):
    seed(repo)
    repo.switch('main', create=True)
    remote = tmp_path / 'remote.git'
    remote.mkdir()
    GitService(remote).run('init', '--bare')
    repo.run('remote', 'add', 'origin', str(remote))
    repo.publish('origin')
    (repo.directory / 'document.xml').write_text('<local-commit/>')
    repo.stage(['document.xml'])
    repo.commit('Keep local commit')
    oid = repo.run('rev-parse', 'HEAD').strip()
    repo.switch('develop')
    repo.switch('origin/main')
    assert repo.status().branch == 'main'
    assert repo.status().upstream == 'origin/main'
    assert repo.run('rev-parse', 'HEAD').strip() == oid
    repo.run('branch', '-m', 'renamed-main')
    repo.switch('develop')
    repo.switch('origin/main')
    assert repo.status().branch == 'renamed-main'
    assert repo.run('rev-parse', 'HEAD').strip() == oid


def test_unstage_before_first_commit_preserves_newer_worktree_content(repo):
    path = repo.directory / 'notes.txt'
    path.write_text('staged version')
    repo.stage(['notes.txt'])
    path.write_text('newer unsaved-to-index version')
    repo.unstage(['notes.txt'])
    assert path.read_text() == 'newer unsaved-to-index version'
    assert repo.status().files[0].index == '?'


def test_remote_selection_is_explicit_when_local_name_looks_like_remote(repo):
    seed(repo)
    repo.run('remote', 'add', 'origin', 'https://example.invalid/project.git')
    repo.run('update-ref', 'refs/remotes/origin/main', 'HEAD')
    repo.switch('origin/main', create=True)
    (repo.directory / 'document.xml').write_text('<local-only/>')
    repo.stage(['document.xml'])
    repo.commit('Local branch with ambiguous name')
    local_oid = repo.run('rev-parse', 'HEAD').strip()
    repo.switch('develop')
    repo.switch('origin/main', remote_reference=True)
    assert repo.status().branch == 'main'
    assert repo.run('rev-parse', '--symbolic-full-name', '@{upstream}').strip() == 'refs/remotes/origin/main'
    assert repo.run('rev-parse', 'refs/heads/origin/main').strip() == local_oid


def test_status_handles_deleted_upstream_and_stash_availability(repo):
    seed(repo)
    repo.run('remote', 'add', 'origin', 'https://example.invalid/project.git')
    repo.run('update-ref', 'refs/remotes/origin/develop', 'HEAD')
    repo.run('branch', '--set-upstream-to', 'origin/develop')
    repo.run('update-ref', '-d', 'refs/remotes/origin/develop')
    assert not repo.status().upstream
    assert not repo.status().has_stash
    (repo.directory / 'notes.txt').write_text('stash me')
    repo.run('stash', 'push', '--include-untracked')
    assert repo.status().has_stash
    repo.run('stash', 'pop')
    assert not repo.status().has_stash
    assert (repo.directory / 'notes.txt').read_text() == 'stash me'
