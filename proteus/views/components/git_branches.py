"""Keyboard-friendly branch/tag quick picker with commit context."""
from datetime import datetime, timezone
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QPalette, QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QLabel,
)
from proteus.application.resources.translator import translate as _
from proteus.application.resources.themes import Themes
from proteus.views.components.git_icons import git_icon


def text(key):
    return _('git.' + key)


def age(date):
    try:
        days = max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(date)).days)
    except ValueError:
        return ''
    return text('today') if days == 0 else text('days_ago').format(days)


class _ReferenceDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        choice = index.data(Qt.ItemDataRole.UserRole)
        return QSize(600, 36 if choice[0] == 'action' else 60)

    def paint(self, painter, option, index):
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.text = ''
        styled.icon = QIcon()
        option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, styled, painter, option.widget)
        action, data, current = index.data(Qt.ItemDataRole.UserRole)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        theme = Themes()
        foreground = theme.color('selection_text', option.palette.color(QPalette.ColorRole.HighlightedText).name()) if selected else option.palette.color(QPalette.ColorRole.Text)
        muted = foreground if selected else option.palette.color(QPalette.ColorRole.PlaceholderText)
        icon_name = 'stage' if action == 'action' and data.startswith('create') else 'branches' if action == 'action' else 'remotes' if data.kind == 'remote' else 'tag' if data.kind == 'tag' else 'branches'
        rect = option.rect
        git_icon(icon_name, option.widget).paint(painter, QRect(rect.left() + 10, rect.top() + 9, 20, 20))
        left, right = rect.left() + 40, rect.right() - 12
        painter.save()
        painter.setClipRect(rect)
        painter.setPen(foreground)
        if action == 'action':
            painter.drawText(QRect(left, rect.top(), right - left, rect.height()), Qt.AlignmentFlag.AlignVCenter, text('picker_' + data))
        else:
            badge = text('reference_' + data.kind)
            badge_width = option.fontMetrics.horizontalAdvance(badge) + 14
            painter.setPen(muted)
            painter.drawText(QRect(right - badge_width, rect.top() + 7, badge_width, 22), Qt.AlignmentFlag.AlignRight, badge)
            title = data.name + (' · ' + text('current_branch') if current else '')
            if data.tracking:
                import re
                counts = re.findall(r'(ahead|behind) (\d+)', data.tracking)
                title += '  ' + ' '.join(('↑' if direction == 'ahead' else '↓') + count for direction, count in counts)
            when = age(data.date)
            if when:
                title += ' · ' + when
            painter.setPen(foreground)
            font = QFont(option.font)
            font.setBold(current)
            painter.setFont(font)
            painter.drawText(QRect(left, rect.top() + 5, max(20, right - left - badge_width), 24), Qt.AlignmentFlag.AlignVCenter,
                             painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, max(20, right - left - badge_width)))
            painter.setFont(option.font)
            painter.setPen(muted)
            detail = f'{data.author} · {data.oid[:7]} · {data.subject}'
            painter.drawText(QRect(left, rect.top() + 30, right - left, 22), Qt.AlignmentFlag.AlignVCenter,
                             option.fontMetrics.elidedText(detail, Qt.TextElideMode.ElideRight, right - left))
        painter.restore()


class GitBranchDialog(QDialog):
    def __init__(self, references, current, parent=None, mode='switch'):
        super().__init__(parent, Qt.WindowType.Popup)
        self.references = references
        self.current = current
        self.mode = mode
        self.choice = None
        self.setObjectName('GitBranchPicker')
        self.setWindowTitle(text('branches'))
        self.resize(760, 510)
        theme = Themes()
        palette = self.palette()
        def color(token, role):
            return theme.color(token, palette.color(role).name()) if theme.current_theme else palette.color(role)
        background = color('window', QPalette.ColorRole.Window)
        foreground = color('text', QPalette.ColorRole.Text)
        border = color('border', QPalette.ColorRole.Mid)
        input_background = color('input_surface', QPalette.ColorRole.Base)
        selection_background = color('selection_bg', QPalette.ColorRole.Highlight)
        selection_foreground = color('selection_text', QPalette.ColorRole.HighlightedText)
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
            palette.setColor(group, QPalette.ColorRole.Highlight, selection_background)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, selection_foreground)
        for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base):
            palette.setColor(role, background)
        for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText):
            palette.setColor(role, foreground)
        self.setPalette(palette)
        self.setStyleSheet(
            f'#GitBranchPicker {{border: 1px solid {border.name()}; background: {background.name()}; color: {foreground.name()};}}'
            f'#GitBranchPicker QListWidget {{border: none; background: {background.name()}; selection-background-color: {selection_background.name()}; selection-color: {selection_foreground.name()};}}'
            f'#GitBranchPicker QListWidget::item:selected {{background: {selection_background.name()}; color: {selection_foreground.name()};}}'
            f'#GitBranchPicker QLabel {{background: transparent; color: {foreground.name()};}}'
            f'#GitBranchPicker QLineEdit {{background: {input_background.name()}; color: {foreground.name()}; border: 1px solid {border.name()}; padding: 6px; border-radius: 4px;}}'
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText(text('branch_search') if mode == 'switch' else text('branch_source') if mode == 'source' else text('detach_reference'))
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setPalette(palette)
        self.list.setItemDelegate(_ReferenceDelegate(self.list))
        self.list.setMouseTracking(True)
        layout.addWidget(self.list)
        hint = QLabel(text('picker_keys'))
        layout.addWidget(hint)
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.activate_current)
        self.list.itemActivated.connect(self.activate)
        self.list.itemClicked.connect(self.activate)
        self.search.installEventFilter(self)
        self.filter('')
        self.search.setFocus()

    def filter(self, query):
        query = query.casefold().strip()
        self.list.clear()
        if self.mode == 'switch':
            for action in ('create', 'create_from', 'detach'):
                item = QListWidgetItem(text('picker_' + action))
                item.setData(Qt.ItemDataRole.UserRole, ('action', action, False))
                self.list.addItem(item)
        kinds = {'local': 0, 'remote': 1, 'tag': 2}
        references = sorted(self.references, key=lambda ref: (kinds[ref.kind], ref.kind != 'local' or ref.name != self.current))
        for ref in references:
            if query and query not in ' '.join((ref.name, ref.author, ref.subject, ref.oid)).casefold():
                continue
            current = ref.kind == 'local' and ref.name == self.current
            item = QListWidgetItem(f'{ref.name} · {ref.author} · {ref.subject}')
            item.setToolTip(f'{ref.full_name}\n{ref.oid}\n{ref.author} · {ref.date}\n{ref.subject}')
            item.setData(Qt.ItemDataRole.UserRole, ('ref', ref, current))
            self.list.addItem(item)
        self.list.setCurrentRow(3 if self.mode == 'switch' and self.list.count() > 3 and query else 0)

    def eventFilter(self, watched, event):
        from PyQt6.QtCore import QEvent
        if watched is self.search and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            delta = 1 if event.key() == Qt.Key.Key_Down else -1
            self.list.setCurrentRow(max(0, min(self.list.count() - 1, self.list.currentRow() + delta)))
            return True
        return super().eventFilter(watched, event)

    def activate_current(self):
        if self.mode == 'detach' and self.list.count() == 0 and self.search.text().strip():
            self.choice = ('detach', self.search.text().strip())
            self.accept()
        else:
            self.activate(self.list.currentItem())

    def activate(self, item):
        if item is None:
            return
        kind, value, _ = item.data(Qt.ItemDataRole.UserRole)
        self.choice = (value, None) if kind == 'action' else ('reference', value)
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        if parent:
            window = QWidget.window(parent)
            center = window.frameGeometry().center()
            screen = window.screen().availableGeometry()
            content_height = 78 + sum(self.list.sizeHintForRow(i) for i in range(self.list.count()))
            self.resize(min(760, screen.width() - 32), min(max(230, content_height), 560, screen.height() - 80))
            self.move(max(screen.left() + 8, min(center.x() - self.width() // 2, screen.right() - self.width() - 8)),
                      max(screen.top() + 8, min(window.frameGeometry().top() + 100, screen.bottom() - self.height() - 8)))
