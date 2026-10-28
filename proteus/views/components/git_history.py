"""Browsable commit history with a painted ancestry graph and commit details."""
from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QSyntaxHighlighter, QTextCharFormat, QPalette, QFontDatabase
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTreeWidget, QTreeWidgetItem,
    QPlainTextEdit, QSplitter, QPushButton, QDialogButtonBox, QStyledItemDelegate, QHeaderView,
)
from proteus.application.resources.translator import translate as _
from proteus.views.components.git_icons import git_icon


def text(key):
    return _('git.' + key)


def graph_rows(commits):
    """Follow parent hashes across topologically ordered rows (including merges)."""
    lanes = []
    rows = []
    for commit in commits:
        incoming = commit.oid in lanes
        if not incoming:
            lanes.append(commit.oid)
        before = tuple(lanes)
        node = lanes.index(commit.oid)
        lanes.pop(node)
        for parent in reversed(commit.parents):
            if parent not in lanes:
                lanes.insert(node, parent)
        after = tuple(lanes)
        through = [(i, after.index(oid)) for i, oid in enumerate(before) if oid != commit.oid and oid in after]
        parents = [after.index(parent) for parent in commit.parents]
        rows.append((node, incoming, through, parents, max(len(before), len(after))))
    return rows


class _GraphDelegate(QStyledItemDelegate):
    colors = ('#438bd1', '#38956e', '#bf7d30', '#9265b8', '#bc637a')

    def sizeHint(self, option, index):
        return QSize(70, 28)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        data = index.data(Qt.ItemDataRole.UserRole + 1)
        if not data:
            return
        node, incoming, through, parents, _ = data
        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        top, middle, bottom = option.rect.top(), option.rect.center().y(), option.rect.bottom() + 1
        def x(lane):
            return option.rect.left() + 12 + lane * 16
        def edge(start, end, y1, y2, color):
            painter.setPen(QPen(QColor(color), 2))
            path = QPainterPath()
            path.moveTo(x(start), y1)
            midpoint = (y1 + y2) / 2
            path.cubicTo(x(start), midpoint, x(end), midpoint, x(end), y2)
            painter.drawPath(path)
        for start, end in through:
            edge(start, end, top, bottom, self.colors[start % len(self.colors)])
        color = self.colors[node % len(self.colors)]
        if incoming:
            edge(node, node, top, middle, color)
        for parent in parents:
            edge(node, parent, middle, bottom, color)
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(option.palette.base())
        painter.drawEllipse(x(node) - 4, middle - 4, 8, 8)
        painter.restore()


class _DiffHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, line):
        color = None
        if line.startswith('+') and not line.startswith('+++'):
            color = '#38956e'
        elif line.startswith('-') and not line.startswith('---'):
            color = '#c75b61'
        elif line.startswith(('@@', 'diff --git', 'commit ')):
            color = '#438bd1'
        if color:
            style = QTextCharFormat()
            style.setForeground(QColor(color))
            self.setFormat(0, len(line), style)


class _Signals(QObject):
    finished = pyqtSignal(object, object, object)


class _ReadJob(QRunnable):
    def __init__(self, key, work):
        super().__init__()
        self.key, self.work = key, work
        self.signals = _Signals()

    def run(self):
        try:
            result = self.work()
        except Exception as error:
            self.signals.finished.emit(self.key, None, error)
        else:
            self.signals.finished.emit(self.key, result, None)


class GitHistoryDialog(QDialog):
    def __init__(self, service, commits, parent=None):
        super().__init__(parent)
        self.service = service
        self.commits = list(commits)
        self._jobs = {}
        self._sequence = 0
        self._requested = None
        self.setWindowTitle(text('history') + ' · ' + service.directory.name)
        self.resize(1050, 720)
        layout = QVBoxLayout(self)
        context = QLabel(str(service.directory))
        context.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        context.setWordWrap(True)
        layout.addWidget(context)
        self.search = QLineEdit()
        self.search.setPlaceholderText(text('history_search'))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        layout.addWidget(self.search)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTreeWidget()
        self.table.setRootIsDecorated(False)
        self.table.setUniformRowHeights(True)
        self.table.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.table.setHeaderLabels([text(key) for key in ('graph', 'commit_subject', 'commit_author', 'commit_date', 'commit_hash', 'commit_refs')])
        self.table.setItemDelegateForColumn(0, _GraphDelegate(self.table))
        self.table.header().setStretchLastSection(False)
        self.table.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 145)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 170)
        self.table.itemSelectionChanged.connect(self.select_commit)
        splitter.addWidget(self.table)
        details = QWidget(self)
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        self.selection_label = QLabel(text('select_commit'))
        self.selection_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addWidget(self.selection_label)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.details.setPlaceholderText(text('select_commit'))
        self.highlighter = _DiffHighlighter(self.details.document())
        details_layout.addWidget(self.details)
        splitter.addWidget(details)
        splitter.setSizes([360, 280])
        layout.addWidget(splitter, 1)
        footer = QHBoxLayout()
        self.count_label = QLabel()
        footer.addWidget(self.count_label)
        footer.addStretch()
        self.load_more = QPushButton(text('load_more_commits'))
        self.load_more.setIcon(git_icon('history', self))
        self.load_more.setEnabled(len(commits) == 200)
        self.load_more.clicked.connect(self.load_page)
        footer.addWidget(self.load_more)
        layout.addLayout(footer)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.populate()

    def populate(self):
        selected = self.table.currentItem()
        oid = selected.data(0, Qt.ItemDataRole.UserRole).oid if selected else None
        self.table.blockSignals(True)
        self.table.clear()
        rows = graph_rows(self.commits)
        target = None
        for commit, graph in zip(self.commits, rows):
            date = commit.date.replace('T', ' ')[:16]
            item = QTreeWidgetItem(self.table, ['', commit.subject, commit.author, date, commit.oid[:8], commit.references])
            item.setData(0, Qt.ItemDataRole.UserRole, commit)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, graph)
            item.setToolTip(1, commit.subject)
            item.setToolTip(3, commit.date)
            item.setToolTip(4, commit.oid)
            item.setToolTip(5, commit.references)
            if commit.oid == oid:
                target = item
        self.table.setColumnWidth(0, max(65, min(240, max((row[-1] for row in rows), default=1) * 16 + 20)))
        self.table.blockSignals(False)
        self.count_label.setText(text('commits_loaded').format(len(self.commits)))
        self.filter(self.search.text())
        if target or self.table.topLevelItemCount():
            self.table.setCurrentItem(target or self.table.topLevelItem(0))

    def filter(self, query):
        query = query.casefold().strip()
        # Filtering out intermediate commits must not imply false ancestry.
        self.table.setColumnHidden(0, bool(query))
        visible = []
        for i in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(i)
            commit = item.data(0, Qt.ItemDataRole.UserRole)
            item.setHidden(bool(query) and query not in ' '.join((commit.subject, commit.author, commit.oid, commit.references)).casefold())
            if not item.isHidden():
                visible.append(item)
        current = self.table.currentItem()
        if visible and (current is None or current.isHidden()):
            self.table.setCurrentItem(visible[0])
        elif not visible:
            self.table.setCurrentItem(None)
            self._requested = None
            self.selection_label.setText(text('select_commit'))
            self.details.clear()

    def read(self, kind, work):
        self._sequence += 1
        key = (kind, self._sequence)
        worker = _ReadJob(key, work)
        self._jobs[key] = worker
        worker.signals.finished.connect(self.loaded)
        QThreadPool.globalInstance().start(worker)
        return key

    def select_commit(self):
        selected = self.table.currentItem()
        if not selected:
            return
        commit = selected.data(0, Qt.ItemDataRole.UserRole)
        self.selection_label.setText(commit.oid + ' · ' + commit.author)
        self.details.setPlainText(text('loading_commit'))
        self._requested = self.read('details', lambda: self.service.commit_details(commit.oid))

    def load_page(self):
        self.load_more.setEnabled(False)
        offset = len(self.commits)
        self.read('page', lambda: self.service.history(skip=offset))

    def loaded(self, key, result, error):
        self._jobs.pop(key, None)
        if key[0] == 'details':
            if key == self._requested:
                self.details.setPlainText(str(error) if error else result[:2_000_000])
        elif error:
            self.count_label.setText(str(error))
            self.load_more.setEnabled(True)
        else:
            self.commits.extend(result)
            self.load_more.setEnabled(len(result) == 200)
            self.populate()
