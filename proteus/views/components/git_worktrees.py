"""Readable overview of repository worktrees."""
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QDialogButtonBox, QHeaderView)
from proteus.application.resources.translator import translate as _
from proteus.views.components.git_icons import git_icon


def text(key):
    return _('git.' + key)


class GitWorktreesDialog(QDialog):
    def __init__(self, worktrees, current, parent=None, can_create=True):
        super().__init__(parent)
        self.action = None
        self.setWindowTitle(text('worktrees'))
        self.resize(820, 360)
        layout = QVBoxLayout(self)
        self.table = QTreeWidget()
        self.table.setRootIsDecorated(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.table.setHeaderLabels([text('worktree_path'), text('worktree_branch'), text('worktree_state')])
        self.table.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for entry in worktrees:
            states = []
            if Path(entry.path).resolve() == Path(current).resolve():
                states.append(text('worktree_current'))
            if entry.bare:
                states.append(text('worktree_bare'))
            if entry.locked is not None:
                states.append(text('worktree_locked'))
            if entry.prunable is not None:
                states.append(text('worktree_prunable'))
            branch = entry.branch or ('HEAD ' + entry.oid[:8] if entry.oid else '—')
            row = QTreeWidgetItem([entry.path, branch, ' · '.join(states)])
            row.setToolTip(0, entry.path)
            row.setToolTip(1, entry.oid)
            row.setToolTip(2, '\n'.join(reason for reason in (entry.locked, entry.prunable) if reason))
            self.table.addTopLevelItem(row)
        layout.addWidget(self.table, 1)
        footer = QHBoxLayout()
        self.create = QPushButton(text('add_worktree'))
        self.create.setAutoDefault(False)
        self.create.setIcon(git_icon('add_worktree', self))
        self.create.setEnabled(can_create)
        self.create.clicked.connect(self.create_worktree)
        footer.addWidget(self.create)
        footer.addStretch()
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        footer.addWidget(close)
        layout.addLayout(footer)

    def create_worktree(self):
        self.action = 'create'
        self.accept()
