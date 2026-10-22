"""Remote management with explicit actions and prefilled editing."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QDialogButtonBox, QFormLayout,
    QLineEdit, QLabel, QHeaderView, QGroupBox)
from proteus.application.resources.translator import translate as _
from proteus.views.components.git_icons import git_icon


def text(key):
    return _('git.' + key)


class GitRemotesDialog(QDialog):
    def __init__(self, remotes, parent=None):
        super().__init__(parent)
        self.command = None
        self.setWindowTitle(text('remotes'))
        self.resize(680, 380)
        layout = QVBoxLayout(self)
        self.list = QTreeWidget()
        self.list.setHeaderLabels([text('remote_name'), text('url')])
        self.list.setRootIsDecorated(False)
        self.list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for name, url in remotes:
            item = QTreeWidgetItem([name, url])
            item.setToolTip(1, url)
            self.list.addTopLevelItem(item)
        layout.addWidget(self.list, 1)
        self.empty = QLabel(text('no_remote'))
        self.empty.setVisible(not remotes)
        layout.addWidget(self.empty)
        row = QHBoxLayout()
        self.add = QPushButton(text('add_remote'))
        self.edit = QPushButton(text('edit_remote'))
        self.remove = QPushButton(text('remove_remote'))
        for button, icon in ((self.add, 'stage'), (self.edit, 'changes'), (self.remove, 'unstage')):
            button.setAutoDefault(False)
            button.setIcon(git_icon(icon, self))
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        self.form = QGroupBox()
        fields = QFormLayout(self.form)
        fields.setContentsMargins(12, 12, 12, 10)
        self.name = QLineEdit()
        self.url = QLineEdit()
        fields.addRow(text('remote_name'), self.name)
        fields.addRow(text('url'), self.url)
        self.save = QPushButton(text('save_remote'))
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel = QPushButton(text('cancel'))
        self.cancel.setAutoDefault(False)
        self.cancel.clicked.connect(self.cancel_form)
        buttons.addWidget(self.cancel)
        buttons.addWidget(self.save)
        fields.addRow(buttons)
        self.form.hide()
        layout.addWidget(self.form)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.add.clicked.connect(lambda: self.show_form(False))
        self.edit.clicked.connect(lambda: self.show_form(True))
        self.remove.clicked.connect(self.remove_selected)
        self.list.itemDoubleClicked.connect(lambda *_: self.show_form(True))
        self.list.itemSelectionChanged.connect(self.update_selection)
        self.name.textChanged.connect(self.validate)
        self.url.textChanged.connect(self.validate)
        self.save.clicked.connect(self.save_form)
        self.update_selection()
        self.validate()

    def update_selection(self):
        selected = bool(self.list.selectedItems())
        self.edit.setEnabled(selected)
        self.remove.setEnabled(selected)
        self.form.hide()

    def show_form(self, editing):
        selected = self.list.selectedItems()
        if editing and not selected:
            return
        self.editing = editing
        self.original_url = selected[0].text(1) if editing else ''
        self.form.setTitle(text('edit_remote' if editing else 'add_remote'))
        self.name.setReadOnly(editing)
        self.name.setText(selected[0].text(0) if editing else '')
        self.url.setText(selected[0].text(1) if editing else '')
        self.form.show()
        self.save.setDefault(True)
        (self.url if editing else self.name).setFocus()
        self.validate()

    def cancel_form(self):
        self.form.hide()
        self.save.setDefault(False)
        self.list.setFocus()

    def validate(self):
        import re
        name = self.name.text().strip()
        editing = getattr(self, 'editing', False)
        duplicate = not editing and any(self.list.topLevelItem(i).text(0) == name for i in range(self.list.topLevelItemCount()))
        valid_name = bool(name and not name.startswith(('-', '/')) and not name.endswith(('/', '.'))
                          and '..' not in name and '@{' not in name and '//' not in name
                          and not re.search(r'[\x00-\x20\x7f~^:?*\[\\]', name)
                          and all(not part.startswith('.') and not part.endswith('.lock') for part in name.split('/')))
        changed = not editing or self.url.text().strip() != getattr(self, 'original_url', '')
        self.save.setEnabled(bool(valid_name and self.url.text().strip() and not duplicate and changed))
        self.save.setToolTip(text('remote_invalid') if not valid_name or duplicate else text('remote_unchanged') if not changed else '')

    def save_form(self):
        if not self.save.isEnabled():
            return
        self.command = ['remote', 'set-url' if self.editing else 'add', '--', self.name.text().strip(), self.url.text().strip()]
        self.accept()

    def remove_selected(self):
        selected = self.list.selectedItems()
        if selected:
            self.command = ['remote', 'remove', '--', selected[0].text(0)]
            self.accept()
