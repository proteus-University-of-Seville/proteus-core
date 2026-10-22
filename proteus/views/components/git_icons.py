"""Use PROTEUS' existing themed bitmap resources for Git controls."""
from proteus.application.resources.icons import Icons, ProteusIconType

_MAIN = {
    'repository': 'open-project', 'init': 'new-project', 'clone': 'clipboard-copy',
    'commit': 'save', 'changes': 'edit', 'fetch': 'redo', 'refresh': 'redo',
    'publish_branch': 'export', 'publish_github': 'new-project', 'history': 'impact-analysis',
    'diff': 'info', 'discard': 'undo', 'revert': 'undo', 'abort': 'undo',
    'git_path': 'settings', 'identity': 'settings', 'remotes': 'settings',
    'copy': 'clipboard-copy', 'stash': 'save', 'apply_stash': 'open-project',
    'tag': 'new-file', 'cherry_pick': 'clipboard-paste', 'reload': 'open-project',
    'more': 'settings', 'warning': 'info', 'trust': 'info', 'clean': 'save', 'continue': 'save',
}
_APP = {
    'branches': 'context-menu-sort', 'create_branch': 'context-menu-clone',
    'rename_branch': 'context-menu-edit', 'delete_branch': 'context-menu-delete',
    'merge': 'context-menu-sort', 'rebase': 'context-menu-sort',
    'pull': 'context-menu-down', 'push': 'context-menu-up',
    'stage': 'add_trace_icon', 'stage_all': 'add_trace_icon', 'stage_hunk': 'add_trace_icon',
    'unstage': 'remove_trace_icon', 'unstage_all': 'remove_trace_icon', 'ignore': 'remove_trace_icon',
    'resolve': 'context-menu-edit', 'worktrees': 'browse_dir_icon', 'add_worktree': 'context-menu-clone',
}


def git_icon(name, widget=None):
    if name in {'refresh', 'fetch', 'remotes', 'history', 'copy', 'branches'}:
        return Icons().icon(ProteusIconType.MainMenu, 'git-' + name)
    if name in _APP:
        return Icons().icon(ProteusIconType.App, _APP[name])
    return Icons().icon(ProteusIconType.MainMenu, _MAIN.get(name, 'edit'))
