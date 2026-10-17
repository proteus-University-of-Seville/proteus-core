"""Dockable source control UI. Git work runs off the GUI thread."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QFontDatabase, QDesktopServices, QGuiApplication, QShortcut, QKeySequence, QPalette
from PyQt6.QtWidgets import (
    QApplication, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QInputDialog, QMessageBox,
    QDialog, QDialogButtonBox, QFileDialog, QMenu, QGridLayout, QSizePolicy, QToolButton, QFrame, QHeaderView, QCheckBox,
)

from proteus.application.events import OpenProjectEvent, SaveProjectEvent, ThemeChangedEvent, GitChangesEvent
from proteus.application.configuration.config import Config
from proteus.application.resources.themes import Themes
from proteus.application.resources.translator import translate as _
from proteus.application.state.manager import StateManager
from proteus.application.clipboard import Clipboard
from proteus.model import PROTEUS_NAME
from proteus.model.abstract_object import ProteusState
from proteus.services.git_service import GitService, GitStatus, GitFile, GitError
from proteus.views.components.git_icons import git_icon


def text(key: str) -> str:
    return _("git." + key)


class _PathLabel(QLabel):
    """Keep long paths readable without forcing the dock wider."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.setMinimumWidth(0)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_path(self, value):
        self.full_text = value
        self.setToolTip(value)
        self._elide()

    def _elide(self):
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideMiddle, max(40, self.width())))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()


class _Signals(QObject):
    finished = pyqtSignal(object, object)


class _Job(QRunnable):
    def __init__(self, work: Callable):
        super().__init__()
        self.work = work
        self.signals = _Signals()

    def run(self):
        try:
            result = self.work()
        except Exception as error:
            self.signals.finished.emit(None, error)
        else:
            self.signals.finished.emit(result, None)


class GitPanel(QDockWidget):
    """Owns repository jobs; never reads or edits the Proteus model in a worker."""
    def __init__(self, window):
        super().__init__(text("title"), window)
        self.setObjectName("GitPanel")
        self.window = window
        self.controller = window._controller
        self.status: GitStatus | None = None
        self.busy = False
        self.blocked = False
        self.directory: Path | None = None
        self._baseline = None
        self.trusted_root = None
        self._pending_refresh = False
        self._job = None
        self._callback = None
        self._changes_disk = False
        self._operation_dock_width = None
        self._job_directory = None
        self._saving = False
        self._quiet = False
        self._after_refresh = None
        self._detected = False
        self._ribbon_labels = []
        self._dock_initialized = False
        self._icon_buttons = []
        self._object_changes = {}
        self._review_names = {}
        self._row_controls = []
        self.setMinimumWidth(290)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        body = QWidget(self)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(8)
        self.repository_card = QFrame()
        self.repository_card.setObjectName("GitRepositoryCard")
        self.repository_card.setStyleSheet(
            "#GitRepositoryCard {background: palette(alternate-base); border: 1px solid palette(mid); border-radius: 6px;}"
            "#GitRepositoryCard QLabel {background: transparent; border: none;}"
        )
        card = QVBoxLayout(self.repository_card)
        card.setContentsMargins(10, 10, 10, 10)
        card.setSpacing(7)
        title_row = QHBoxLayout()
        self.repository_icon = QLabel()
        self.repository_icon.setFixedSize(30, 30)
        title_row.addWidget(self.repository_icon)
        title = QVBoxLayout()
        title.setSpacing(1)
        self.repository_kind = QLabel(text("repository"))
        title.addWidget(self.repository_kind)
        self.repository_label = QLabel(text("open_project"))
        font = self.repository_label.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() + 1)
        self.repository_label.setFont(font)
        self.repository_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title.addWidget(self.repository_label)
        title_row.addLayout(title, 1)
        self.copy_path = QToolButton()
        self.copy_path.setAutoRaise(True)
        self.copy_path.setToolTip(text("copy_path"))
        self.copy_path.setAccessibleName(text("copy_path"))
        self.copy_path.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.repository_path.full_text))
        self._icon_buttons.append((self.copy_path, "copy"))
        title_row.addWidget(self.copy_path)
        card.addLayout(title_row)
        self.repository_path = _PathLabel()
        card.addWidget(self.repository_path)
        remote_row = QHBoxLayout()
        self.remote_name = QLabel()
        self.remote_name.setStyleSheet("font-weight: bold;")
        remote_row.addWidget(self.remote_name)
        self.remote_label = QLabel()
        self.remote_label.setWordWrap(True)
        self.remote_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        remote_row.addWidget(self.remote_label, 1)
        card.addLayout(remote_row)
        self.scope_label = QLabel()
        self.scope_label.setWordWrap(True)
        self.scope_label.setVisible(False)
        card.addWidget(self.scope_label)
        row = QHBoxLayout()
        self.branch_button = QPushButton(text("branches"))
        self.branch_button.clicked.connect(lambda: self.guard(self.choose_branch))
        row.addWidget(self.branch_button, 1)
        self._icon_buttons.append((self.branch_button, "branches"))
        self.refresh_button = QToolButton()
        self.refresh_button.setAutoRaise(True)
        self.refresh_button.setToolTip(text("refresh"))
        self._icon_buttons.append((self.refresh_button, "refresh"))
        self.refresh_button.clicked.connect(self.refresh)
        row.addWidget(self.refresh_button)
        self.more_button = QToolButton()
        self.more_button.setAutoRaise(True)
        self.more_button.setToolTip(text("more_actions"))
        self.more_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._icon_buttons.append((self.more_button, "more"))
        row.addWidget(self.more_button)
        card.addLayout(row)
        layout.addWidget(self.repository_card)
        self.menu = QMenu(self)
        self.menu.setToolTipsVisible(True)
        self.more_button.setMenu(self.menu)
        self.actions = {}
        for key, slot in (
            ("init", self.initialize), ("clone", self.clone), ("commit", self.commit),
            ("branches", self.choose_branch), ("create_branch", self.create_branch),
            ("rename_branch", self.rename_branch), ("delete_branch", self.delete_branch),
            ("fetch", lambda: self.command(["fetch", "--all", "--prune"])),
            ("pull", self.pull), ("push", self.push), ("publish_branch", self.publish),
            ("remotes", self.remotes), ("identity", self.identity),
            ("history", self.history), ("merge", lambda: self.integrate("merge")),
            ("rebase", lambda: self.integrate("rebase")),
            ("continue", self.continue_operation), ("abort", self.abort_operation),
            ("stash", self.stash), ("apply_stash", self.apply_stash),
            ("revert", lambda: self.commit_action("revert")),
            ("cherry_pick", lambda: self.commit_action("cherry-pick")),
            ("tag", self.tag), ("publish_github", self.publish_github),
            ("git_path", self.set_git_path), ("reload", self.reload),
            ("stage_all", self.stage_all), ("unstage_all", self.unstage_all),
            ("stage_hunk", self.stage_hunk), ("ignore", self.ignore),
            ("worktrees", self.worktrees), ("add_worktree", self.add_worktree), ("trust", self.trust_repository),
        ):
            action = self.menu.addAction(text(key))
            action.setToolTip(text("tip_" + key) if key in {"fetch", "pull", "push", "publish_branch", "publish_github", "commit"} else text(key))
            action.setStatusTip(action.toolTip())
            action.triggered.connect(lambda checked=False, callback=slot: self.guard(callback))
            self.actions[key] = action
        groups = {
            "repository": ("init", "clone", "remotes", "identity", "git_path", "publish_github", "reload", "trust"),
            "branches": ("branches", "create_branch", "rename_branch", "delete_branch", "worktrees", "add_worktree"),
            "synchronize": ("fetch", "pull", "push", "publish_branch"),
            "changes": ("commit", "stage_all", "unstage_all", "stage_hunk", "ignore", "stash", "apply_stash"),
            "history": ("history", "merge", "rebase", "revert", "cherry_pick", "tag"),
            "conflicts": ("continue", "abort"),
        }
        separators = {'repository': {'clone', 'identity', 'publish_github'},
                      'branches': {'delete_branch'}, 'synchronize': {'push'},
                      'changes': {'commit', 'unstage_all', 'ignore'},
                      'history': {'history', 'rebase'}}
        self.submenus = {}
        for group, keys in groups.items():
            submenu = self.menu.addMenu(text(group))
            submenu.setToolTipsVisible(True)
            self.submenus[group] = submenu
            for key in keys:
                self.menu.removeAction(self.actions[key])
                submenu.addAction(self.actions[key])
                if key in separators.get(group, set()):
                    submenu.addSeparator()
        self.git_executable = Config().app_settings.config_parser.get("git", "executable", fallback="git")
        self.message = QPlainTextEdit()
        self.message.setPlaceholderText(text("message"))
        self.message.setMaximumHeight(85)
        self.message.setAccessibleName(text("message"))
        self.message.textChanged.connect(self._update_actions)
        layout.addWidget(self.message)
        self.commit_button = QPushButton(text("commit"))
        self.commit_button.clicked.connect(lambda: self.guard(self.commit))
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(lambda: self.guard(self.commit) if self.commit_button.isEnabled() else None)
        self._icon_buttons.append((self.commit_button, "commit"))
        layout.addWidget(self.commit_button)
        self.tree = QTreeWidget()
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)
        self.empty_state = QLabel(text("open_project"))
        self.empty_state.setWordWrap(True)
        layout.addWidget(self.empty_state)
        self.empty_actions = QWidget()
        empty_layout = QHBoxLayout(self.empty_actions)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        for key in ("init", "clone"):
            button = QToolButton()
            button.setDefaultAction(self.actions[key])
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            empty_layout.addWidget(button)
        layout.addWidget(self.empty_actions)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(1, 64)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.itemDoubleClicked.connect(lambda *_: self.guard(self.preview))
        self.tree.itemSelectionChanged.connect(self._update_actions)
        self.tree.itemClicked.connect(self.change_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.file_context_menu)
        self.highlight_toggle = QCheckBox(text("highlight_document"))
        self.highlight_toggle.setChecked(True)
        self.highlight_toggle.setToolTip(text("highlight_help"))
        self.highlight_toggle.toggled.connect(self.publish_highlights)
        layout.addWidget(self.highlight_toggle)
        layout.addWidget(self.tree)
        file_actions = QGridLayout()
        self.file_buttons = []
        self._file_keys = []
        for key, slot in (("stage", self.stage), ("unstage", self.unstage),
                          ("diff", self.preview), ("resolve", self.resolve), ("discard", self.discard)):
            button = QPushButton(text(key))
            button.clicked.connect(lambda checked=False, callback=slot: self.guard(callback))
            index = len(self.file_buttons)
            file_actions.addWidget(button, index // 3, index % 3)
            self.file_buttons.append(button)
            self._file_keys.append(key)
            self._icon_buttons.append((button, key))
            button.setToolTip(text(key))
        layout.addLayout(file_actions)
        self.feedback = QLabel()
        self.feedback.setTextFormat(Qt.TextFormat.PlainText)
        self.feedback.setWordWrap(True)
        self.feedback.setMinimumWidth(0)
        self.feedback.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.feedback.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.feedback.hide()
        layout.addWidget(self.feedback)
        self.setWidget(body)
        self.indicator = QPushButton(text("title"))
        self.indicator.clicked.connect(lambda: self.guard(self.choose_branch))
        self._icon_buttons.append((self.indicator, "branches"))
        window.statusBar().addPermanentWidget(self.indicator)
        OpenProjectEvent().connect(self.project_opened)
        SaveProjectEvent().connect(self.project_saved)
        self.controller._git_validate_save = self.validate_save
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        ThemeChangedEvent().connect(self.update_icons)
        self.update_icons()
        self._update_actions()
        self.hide()

    def set_feedback(self, message):
        self.feedback.setText(message)
        self.feedback.setToolTip(message)
        self.feedback.setVisible(bool(message))

    def reveal(self):
        self.show()
        if not self._dock_initialized:
            self.window.resizeDocks([self], [self.minimumWidth()], Qt.Orientation.Horizontal)
            self._dock_initialized = True
        self.raise_()
        self.refresh()

    def project_opened(self):
        directory = StateManager().current_project_path
        if directory != self.directory:
            self.status = None
            self._detected = False
            self._row_controls = []
            self.tree.clear()
        self.directory = directory
        self._object_changes = {}
        self._review_names.clear()
        self.publish_highlights()
        self._render_repository()
        self.blocked = False
        self.controller._git_write_blocked = False
        self._baseline = self.fingerprint(self.directory)
        # Let project creation finish before starting a child process in its
        # folder (Windows prevents removing a running process's cwd).
        QTimer.singleShot(250, self.refresh)

    @staticmethod
    def fingerprint(directory):
        if not directory:
            return ()
        paths = [directory / "proteus.xml"]
        # Only XML is cached in the document model. AssetEdit intentionally
        # copies images straight to disk while its properties dialog is open.
        for folder in ("objects",):
            if (directory / folder).exists():
                paths.extend(path for path in (directory / folder).rglob("*.xml") if path.is_file())
        result = []
        for path in sorted(paths):
            try:
                stat = path.stat()
                result.append((str(path), stat.st_mtime_ns, stat.st_size))
            except FileNotFoundError:
                pass
        return tuple(result)

    def project_saved(self):
        self._baseline = self.fingerprint(self.directory)
        self.refresh()

    def service(self, directory=None):
        root = directory or (self.status.root if self.status else self.directory)
        return GitService(root, self.git_executable, self.trusted_root)

    def job(self, work, callback=None, changes_disk=False, quiet=False):
        if self.busy:
            return
        self.busy = True
        self._job_directory = self.directory
        self._callback = callback
        self._quiet = quiet
        self._changes_disk = changes_disk
        self._operation_dock_width = self.width() if changes_disk else None
        if not quiet:
            self.set_feedback(text("working"))
        if changes_disk:
            self.controller._git_operation_active = True
            self.window.project_container.setEnabled(False)
            self.window.main_menu.setEnabled(False)
        if not quiet:
            self._update_actions()
        def invoke():
            if not changes_disk:
                return work()
            error = None
            result = None
            try:
                result = work()
            except Exception as failure:
                error = failure
            try:
                state = self.service().status()
            except Exception as failure:
                return result, error or failure, None
            return result, error, state
        self._job = _Job(invoke)
        self._job.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self._job)

    def _finished(self, result, error):
        callback, changes_disk, quiet = self._callback, self._changes_disk, self._quiet
        dock_width = self._operation_dock_width
        job_directory = self._job_directory
        self._callback = None
        self._job = None
        self.busy = False
        if not changes_disk and job_directory != self.directory:
            self._after_refresh = None
            self._pending_refresh = False
            self._update_actions()
            self.refresh()
            return
        if error or not quiet:
            self.set_feedback(str(error) if error else "")
        if changes_disk:
            self.controller._git_operation_active = False
            if result is not None:
                result, error, state = result
                self._reload(state)
            else:
                self.blocked = True
            if error:
                self.set_feedback(str(error))
        try:
            if not error and callback:
                callback(result)
        except Exception as failure:
            self.set_feedback(str(failure))
        if error and not quiet:
            QMessageBox.warning(self, text("title"), str(error))
        if dock_width and self.isVisible() and not self.isFloating():
            # Rebuilding the central editor schedules a layout after reload.
            # Restore the user's width once that layout has been applied.
            QTimer.singleShot(0, lambda width=dock_width: self.window.resizeDocks([self], [width], Qt.Orientation.Horizontal) if self.isVisible() and not self.isFloating() else None)
        self._update_actions()
        deferred, self._after_refresh = self._after_refresh, None
        if deferred:
            self.guard(deferred)
        if self._pending_refresh and not self.busy:
            self._pending_refresh = False
            self.refresh()

    def refresh(self):
        if not self.directory:
            self._update_actions()
            return
        if self.busy or self._saving or QApplication.activeModalWidget() is not None:
            self._pending_refresh = True
            return
        # Capture path now. Switching projects while a read runs must not
        # display a stale repository snapshot in the new project.
        directory = self.directory
        try:
            service = self.service(directory)
        except GitError as error:
            self.set_feedback(str(error))
            self._update_actions()
            return
        self.job(service.status, lambda state: self._show_status(state) if directory == self.directory else None, quiet=True)

    @staticmethod
    def remote_display(url):
        """Display repository location without embedded HTTPS credentials."""
        from urllib.parse import urlsplit, urlunsplit
        if "://" in url:
            try:
                parts = urlsplit(url)
                host = parts.hostname or ""
                if ":" in host:
                    host = "[" + host + "]"
                if parts.port:
                    host += ":" + str(parts.port)
                return urlunsplit((parts.scheme, host, parts.path, "", ""))
            except ValueError:
                # Invalid ports / IPv6 must not interrupt status rendering or
                # expose credentials by falling back to the original URL.
                return text("invalid_remote_url")
        if "@" in url and ":" in url:
            return url.split("@", 1)[1].replace(":", "/", 1)
        return url

    def _render_repository(self):
        state = self.status
        root = state.root if state else self.directory
        name = root.name if root else text("no_project")
        self.repository_label.setText(name)
        self.repository_path.set_path(str(root) if root else "")
        self.repository_label.setToolTip(str(root) if root else "")
        if state:
            remote = next((pair for pair in state.remotes if pair[0] == "origin"), state.remotes[0] if state.remotes else None)
            location = self.remote_display(remote[1]) if remote else ""
            self.remote_name.setText(remote[0] if remote else "")
            self.remote_label.setText(location.removeprefix("https://").removeprefix("http://").removesuffix(".git") if remote else text("no_remote"))
            self.remote_label.setToolTip(location)
            counts = f"  ↑ {state.ahead}  ↓ {state.behind}" if state.upstream else ""
            self.branch_button.setText(state.branch + counts)
            self.branch_button.setToolTip(text("branches") + " · " + (state.upstream or text("branch_unpublished")))
            summary = text("clean_worktree") if not state.files else text("one_file_changed") if len(state.files) == 1 else text("files_changed").format(len(state.files))
            self.summary_label.setText(summary)
            try:
                relative = self.directory.resolve().relative_to(state.root.resolve())
            except ValueError:
                relative = self.directory
            nested = str(relative) != "."
            self.scope_label.setText(text("project_location").format(relative))
            self.scope_label.setToolTip(text("scope"))
            self.scope_label.setVisible(nested)
            self.indicator.setText(f"{name} / {state.branch}" + counts)
            detail = state.operation or (state.upstream if state.upstream else text("branch_unpublished"))
            self.empty_state.setText(text("clean_worktree"))
        else:
            detail = text("detecting") if root and not self._detected else text("no_repository") if root else text("open_project")
            self.remote_name.clear()
            self.remote_label.setText(detail)
            self.branch_button.setText(text("branches"))
            self.summary_label.clear()
            self.scope_label.hide()
            self.indicator.setText(name + " · Git")
            self.empty_state.setText(text("no_repository_help") if root and self._detected else detail)
        self.indicator.setToolTip((str(root) + "\n" if root else "") + detail)
        self.summary_label.setVisible(bool(state and state.files))
        self.empty_state.setVisible(not state or not state.files)
        self.empty_actions.setVisible(state is None)
        for repository, branch in self._ribbon_labels:
            repository.set_path(name)
            repository.setToolTip(str(root) if root else "")
            branch.set_path(state.branch if state else detail)
            branch.setToolTip(self.remote_label.text())

    def _show_status(self, state):
        previous = self.status
        self.status = state
        self._detected = True
        stamp = self.fingerprint(self.directory)
        if self._baseline is not None and stamp != self._baseline and not self.blocked:
            self.blocked = True
            self.controller._git_write_blocked = True
            self.window.project_container.setEnabled(False)
            self.window.main_menu.setEnabled(False)
            self.set_feedback(text("external_changes"))
        self._render_repository()
        self.update_document_changes()
        # Preserve actual items, keyboard focus, selection, expansion and scroll
        # when Git reports the same files. Polling must not rebuild the view.
        if previous is not None and state is not None and previous.files == state.files:
            for group_index in range(self.tree.topLevelItemCount()):
                group = self.tree.topLevelItem(group_index)
                for i in range(group.childCount()):
                    item = group.child(i)
                    file = item.data(0, Qt.ItemDataRole.UserRole)[0]
                    obj = self.object_for_file(file)
                    name = str(obj.get_property(PROTEUS_NAME).value) if obj else self._review_names.get(file.path, Path(file.path).name)
                    item.setText(0, name)
                    item.setToolTip(0, name + "\n" + file.path)
            self._update_actions()
            return
        selected = {(data[0].path, data[1]) for item in self.tree.selectedItems()
                    if (data := item.data(0, Qt.ItemDataRole.UserRole))}
        collapsed = {self.tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole + 1)
                     for i in range(self.tree.topLevelItemCount()) if not self.tree.topLevelItem(i).isExpanded()}
        scroll = self.tree.verticalScrollBar().value()
        self.tree.setUpdatesEnabled(False)
        self.tree.blockSignals(True)
        try:
            self._row_controls = []
            self.tree.clear()
            groups = {}
            for key in ("conflicts", "staged", "changes"):
                group = QTreeWidgetItem(self.tree, [text(key)])
                group.setData(0, Qt.ItemDataRole.UserRole + 1, key)
                group.setFlags(group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                groups[key] = group
            for file in state.files if state else ():
                kinds = ["conflicts"] if file.conflicted else []
                if not file.conflicted:
                    if file.index not in " ?":
                        kinds.append("staged")
                    if file.worktree != " " or file.index == "?":
                        kinds.append("changes")
                for kind in kinds:
                    staged = kind == "staged"
                    path = Path(file.path)
                    folder = str(path.parent) if str(path.parent) != "." else ""
                    obj = self.object_for_file(file)
                    name = str(obj.get_property(PROTEUS_NAME).value) if obj else self._review_names.get(file.path, path.name)
                    item = QTreeWidgetItem(groups[kind], [name, ""])
                    item.setIcon(0, git_icon("warning" if file.conflicted else "stage" if file.index in "A?" else "changes", self))
                    item.setToolTip(0, name + "\n" + file.path + ("\n" + file.original if file.original else ""))
                    item.setToolTip(1, file.path)
                    item.setData(0, Qt.ItemDataRole.UserRole, (file, staged))
                    item.setSelected((file.path, staged) in selected)
                    self.add_file_controls(item, file, staged)
            for key, group in groups.items():
                group.setText(0, f"{text(key)} ({group.childCount()})")
                group.setHidden(group.childCount() == 0)
                group.setExpanded(key not in collapsed)
            self.tree.verticalScrollBar().setValue(scroll)
        finally:
            self.tree.blockSignals(False)
            self.tree.setUpdatesEnabled(True)
        self._update_actions()

    def add_file_controls(self, item, file, staged):
        controls = QWidget()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for key in ("diff", "resolve" if file.conflicted else "unstage" if staged else "stage"):
            button = QToolButton()
            button.setAutoRaise(True)
            button.setIcon(git_icon(key, self))
            button.setIconSize(QSize(16, 16))
            button.setToolTip(text("review_document") if key == "diff" else text(key))
            button.setAccessibleName(button.toolTip())
            def activate(checked=False, action=key, row=item, entry=file):
                self.tree.clearSelection()
                row.setSelected(True)
                if action == "diff":
                    self.guard(self.preview)
                elif action == "resolve":
                    self.guard(self.resolve)
                else:
                    self.guard(lambda: self.stage_reviewed_file(entry, action == "unstage"))
            button.clicked.connect(activate)
            layout.addWidget(button)
            self._row_controls.append((key, button))
        self.tree.setItemWidget(item, 1, controls)

    def object_for_file(self, file):
        if not self.status or not self.directory:
            return None
        path = (self.status.root / file.path).resolve()
        project = self.controller.get_current_project()
        if project is None:
            return None
        if path == Path(project.path).resolve():
            return project
        if path.parent != (self.directory / "objects").resolve() or path.suffix.lower() != ".xml":
            return None
        try:
            return self.controller.get_element(path.stem)
        except (KeyError, AssertionError, ValueError):
            return None

    def update_document_changes(self):
        changes = {}
        for file in self.status.files if self.status else ():
            obj = self.object_for_file(file)
            if obj:
                changes[str(obj.id)] = "added" if file.index in "A?" else "modified"
        self._object_changes = changes
        self.publish_highlights()

    def publish_highlights(self, *_):
        changes = self._object_changes if self.highlight_toggle.isChecked() else {}
        if changes != GitChangesEvent().changes:
            GitChangesEvent().notify(changes)

    def change_clicked(self, item, _column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and len(self.selected()) == 1:
            self.navigate_to_file(data[0])

    def navigate_to_file(self, file):
        if self.blocked or (self.busy and not self._quiet):
            return
        obj = self.object_for_file(file)
        if not obj or obj.state == ProteusState.DEAD or not hasattr(obj, "get_document"):
            return
        document = obj.get_document()
        state = StateManager()
        if state.get_current_document() != document.id:
            state.set_current_document(document.id)
        state.set_current_object(obj.id, document.id)

    def _update_actions(self):
        locked = self.busy and not self._quiet
        ready = self.status is not None and not locked
        for key, action in self.actions.items():
            action.setEnabled(ready)
        self.actions["reload"].setEnabled(bool(self.directory) and not locked)
        self.actions["clone"].setEnabled(not locked)
        self.actions["git_path"].setEnabled(not locked)
        self.actions["trust"].setEnabled(bool(self.directory) and not locked)
        self.actions["init"].setEnabled(bool(self.directory) and self._detected and self.status is None and not locked)
        self.actions["publish_branch"].setEnabled(ready and self.status.has_commits and bool(self.status.remotes) and not self.status.upstream and not self.status.branch.startswith("HEAD "))
        self.actions['publish_branch'].setToolTip(text('push_first_commit') if self.status and not self.status.has_commits else text('configure_remote_first') if self.status and not self.status.remotes else text('tip_publish_branch'))
        self.branch_button.setEnabled(ready)
        self.indicator.setEnabled(ready)
        self.more_button.setEnabled(not locked)
        self.refresh_button.setEnabled(bool(self.directory) and not locked)
        files = self.status.files if self.status else ()
        detached = bool(self.status and self.status.branch.startswith('HEAD '))
        for key in ('rename_branch', 'delete_branch'):
            self.actions[key].setEnabled(ready and not detached)
        for key in ('history', 'tag', 'merge', 'rebase', 'revert', 'cherry_pick', 'add_worktree'):
            self.actions[key].setEnabled(ready and self.status.has_commits)
        self.actions['fetch'].setEnabled(ready and bool(self.status.remotes))
        self.actions['pull'].setEnabled(ready and bool(self.status.upstream) and not detached and not self.blocked)
        self.actions['push'].setEnabled(ready and not detached)
        self.actions['fetch'].setToolTip(text('configure_remote_first') if self.status and not self.status.remotes else text('tip_fetch'))
        self.actions['pull'].setToolTip(text('tracking_required') if self.status and not self.status.upstream else text('tip_pull'))
        self.submenus['conflicts'].menuAction().setVisible(bool(self.status and self.status.operation))
        can_commit = ready and not self.blocked and not any(f.conflicted for f in files) and bool(files)
        self.commit_button.setEnabled(can_commit)
        self.actions["commit"].setEnabled(can_commit)
        selected = self.selected()
        conditions = {
            "stage": not self.blocked and any(not staged for _, staged in selected),
            "unstage": any(staged for _, staged in selected),
            "diff": bool(selected),
            "resolve": any(file.conflicted for file, _ in selected),
            "discard": any(file.index != "?" and not file.conflicted and file.worktree != " " for file, _ in selected),
        }
        for key, button in zip(self._file_keys, self.file_buttons):
            button.setEnabled(ready and conditions[key])
        for key in ("continue", "abort"):
            self.actions[key].setEnabled(ready and bool(self.status.operation))
        self.actions['continue'].setEnabled(ready and bool(self.status.operation) and not any(file.conflicted for file in files))
        self.actions["stage_all"].setEnabled(ready and not self.blocked and any(file.worktree != ' ' for file in files))
        self.actions["unstage_all"].setEnabled(ready and any(file.index not in ' ?' and not file.conflicted for file in files))
        self.actions["stash"].setEnabled(ready and self.status.has_commits and not self.blocked and bool(files) and not any(file.conflicted for file in files))
        self.actions["apply_stash"].setEnabled(ready and not self.blocked and self.status.has_stash and not files)
        self.actions["apply_stash"].setToolTip(text('clean_first') if files else text('apply_stash') if self.status and self.status.has_stash else text('no_stashes'))
        self.actions["stage_hunk"].setEnabled(ready and not self.blocked and len(selected) == 1 and not selected[0][1] and selected[0][0].worktree == 'M' and not selected[0][0].conflicted and not selected[0][0].original)
        self.actions['ignore'].setEnabled(ready and not self.blocked and any(file.index == '?' for file, _ in selected))
        container = getattr(self.window.project_container, 'views_container', None)
        if container is not None:
            by_path = {file.path: file for file in files}
            for index in range(container.count()):
                review = container.widget(index)
                key = getattr(review, 'git_review_key', None)
                if key is None:
                    continue
                path, staged = key
                file = by_path.get(path)
                available = bool(file and not file.conflicted and (file.index not in ' ?' if staged else file.worktree != ' '))
                review.stage.setEnabled(ready and not self.blocked and available)
        for action in self.actions.values():
            action.setStatusTip(action.toolTip())
        self.message.setEnabled(not locked)
        for key, button in self._row_controls:
            button.setEnabled(ready and (not self.blocked or key in {"diff", "resolve"}))

    def file_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item and item.data(0, Qt.ItemDataRole.UserRole) and not item.isSelected():
            self.tree.clearSelection()
            item.setSelected(True)
        if not self.selected():
            return
        menu = QMenu(self)
        for key, button in zip(self._file_keys, self.file_buttons):
            action = menu.addAction(button.icon(), button.text())
            action.setEnabled(button.isEnabled())
            action.triggered.connect(button.click)
        menu.addSeparator()
        menu.addAction(self.actions["stage_hunk"])
        menu.addAction(self.actions["ignore"])
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def update_icons(self, *_):
        # Use theme tokens explicitly: palette(alternate-base) can retain the
        # platform's light color when a dark theme is applied through QSS.
        theme = Themes()
        palette = self.palette()
        background = theme.color("chrome_surface", palette.color(QPalette.ColorRole.Window).name()) if theme.current_theme else palette.color(QPalette.ColorRole.Window)
        foreground = theme.color("text", palette.color(QPalette.ColorRole.WindowText).name()) if theme.current_theme else palette.color(QPalette.ColorRole.WindowText)
        border = theme.color("border", palette.color(QPalette.ColorRole.Mid).name()) if theme.current_theme else palette.color(QPalette.ColorRole.Mid)
        self.repository_card.setStyleSheet(
            f"#GitRepositoryCard {{background: {background.name()}; color: {foreground.name()}; border: 1px solid {border.name()}; border-radius: 6px;}}"
            f"#GitRepositoryCard QLabel {{background: transparent; color: {foreground.name()}; border: none;}}"
        )
        self.repository_icon.setPixmap(git_icon("repository", self).pixmap(28, 28))
        for key, action in self.actions.items():
            action.setIcon(git_icon(key, self))
        for button, key in self._icon_buttons:
            button.setIcon(git_icon(key, self))
            button.setIconSize(QSize(18, 18))
        self.toggleViewAction().setIcon(git_icon("changes", self))
        for key, button in self._row_controls:
            button.setIcon(git_icon(key, self))
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for index in range(group.childCount()):
                item = group.child(index)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    item.setIcon(0, git_icon("warning" if data[0].conflicted else "changes", self))

    def create_ribbon(self):
        ribbon = QWidget()
        layout = QHBoxLayout(ribbon)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        show = self.toggleViewAction()
        show.setText(text("panel"))
        show.setToolTip(text("panel_tip"))
        for caption, actions in (
            ("changes", [show, self.actions["commit"]]),
            ("synchronize", [self.actions[key] for key in ("fetch", "pull", "push", "publish_branch")]),
            ("repository", [self.actions[key] for key in ("branches", "remotes", "history")]),
        ):
            group = QWidget()
            vertical = QVBoxLayout(group)
            vertical.setContentsMargins(0, 0, 0, 0)
            vertical.setSpacing(2)
            buttons = QHBoxLayout()
            buttons.setSpacing(2)
            for action in actions:
                button = QToolButton()
                button.setDefaultAction(action)
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                button.setIconSize(QSize(32, 32))
                button.setMinimumWidth(58)
                buttons.addWidget(button)
            vertical.addLayout(buttons)
            label = QLabel(text(caption))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vertical.addWidget(label)
            layout.addWidget(group)
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.VLine)
            layout.addWidget(separator)
        context = QWidget()
        context_layout = QVBoxLayout(context)
        context_layout.setContentsMargins(0, 0, 0, 0)
        repository = _PathLabel()
        font = repository.font()
        font.setBold(True)
        repository.setFont(font)
        branch = _PathLabel()
        context_layout.addWidget(repository)
        context_layout.addWidget(branch)
        self._ribbon_labels.append((repository, branch))
        layout.addWidget(context, 1)
        self._render_repository()
        return ribbon

    def guard(self, callback):
        if self.busy and self._quiet:
            # Execute a click after the short background read, rather than
            # flashing disabled controls or silently dropping the user's click.
            self._after_refresh = callback
            return
        try:
            callback()
        except Exception as error:
            QMessageBox.warning(self, text("title"), str(error))

    def selected(self):
        return [item.data(0, Qt.ItemDataRole.UserRole) for item in self.tree.selectedItems()
                if item.data(0, Qt.ItemDataRole.UserRole)]

    def ask(self, key, value=""):
        answer, ok = QInputDialog.getText(self, text("title"), text(key), text=value)
        return answer.strip() if ok and answer.strip() else None

    def pick(self, key, options):
        if not options:
            QMessageBox.information(self, text("title"), text("empty"))
            return None
        answer, ok = QInputDialog.getItem(self, text("title"), text(key), options, 0, False)
        return answer if ok else None

    def confirm(self, message):
        return QMessageBox.question(self, text("title"), message,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def validate_save(self):
        if self._baseline is not None and self.fingerprint(self.directory) != self._baseline:
            self.blocked = True
            self.controller._git_write_blocked = True
            self.window.project_container.setEnabled(False)
            self.window.main_menu.setEnabled(False)
            self.set_feedback(text("external_changes"))
            raise GitError(text("external_changes"))

    def saved(self):
        if self._baseline is not None and self.fingerprint(self.directory) != self._baseline:
            self.blocked = True
            self.controller._git_write_blocked = True
            self.window.project_container.setEnabled(False)
            self.window.main_menu.setEnabled(False)
        if self.blocked:
            return not self.controller.check_unsaved_changes() or self.confirm(text("discard_memory"))
        if self.controller.check_unsaved_changes():
            if not self.confirm(text("save_first")):
                return False
            try:
                self._saving = True
                self.controller.save_project()
            except Exception as error:
                QMessageBox.warning(self, text("title"), str(error))
                return False
            finally:
                self._saving = False
        return True

    def command(self, args, changes_disk=False, require_clean=False):
        if not self.status or self.busy:
            return
        if changes_disk and not self.saved():
            return
        service = self.service()
        def work():
            state = service.status()
            if require_clean and state.files:
                raise GitError(text("clean_first"))
            return service.run(*args)
        self._pending_refresh = True
        label_key = {'branch': 'branches', 'remote': 'remotes', 'restore': 'discard',
                     'cherry-pick': 'cherry_pick', 'worktree': 'worktrees'}.get(args[0], args[0])
        if args[0] == 'branch':
            label_key = {'-m': 'rename_branch', '-d': 'delete_branch'}.get(args[1], 'branches')
        elif args[0] == 'remote':
            label_key = {'add': 'add_remote', 'set-url': 'edit_remote', 'remove': 'remove_remote'}.get(args[1], 'remotes')
        elif args[:2] == ['stash', 'apply']:
            label_key = 'apply_stash'
        self.job(work, lambda output: self.report_output(output, text(label_key)), changes_disk=changes_disk)

    def report_output(self, output, label=None):
        output = str(output or '').strip()
        if label:
            self.set_feedback(text('operation_completed').format(label.rstrip('… .')))
        elif output:
            self.set_feedback(output.splitlines()[0][:180])
        self.feedback.setToolTip(output)

    def show_output(self, output, title=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title or text("title"))
        dialog.resize(850, 550)
        layout = QVBoxLayout(dialog)
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        editor.setPlainText(output)
        layout.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _reload(self, state):
        dock_width = self.width()
        try:
            if state and any(file.conflicted for file in state.files):
                raise GitError(text("resolve_first"))
            # Preload into a separate service before replacing live state.
            self.controller.reload_project_from_disk(str(self.directory))
            self.blocked = False
            self._baseline = self.fingerprint(self.directory)
        except Exception as error:
            self.blocked = True
            self.set_feedback(text("reload_failed") + "\n" + str(error))
        self.controller._git_write_blocked = self.blocked
        self.window.project_container.setEnabled(not self.blocked)
        self.window.main_menu.setEnabled(not self.blocked)
        if self.isVisible() and not self.isFloating():
            self.window.resizeDocks([self], [dock_width], Qt.Orientation.Horizontal)

    def stage(self):
        if self.blocked or not self.saved() or self.busy:
            return
        paths = list(dict.fromkeys(file.path for file, staged in self.selected() if not staged))
        if paths:
            service = self.service()
            self._pending_refresh = True
            self.job(lambda: service.stage(paths))

    def unstage(self):
        paths = list(dict.fromkeys(path for file, staged in self.selected() if staged
                                   for path in (file.path, file.original) if path))
        if paths:
            service = self.service()
            self._pending_refresh = True
            self.job(lambda: service.unstage(paths))

    def pending_choice(self, key, choices):
        box = QMessageBox(self)
        box.setWindowTitle(text('title'))
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(text(key))
        buttons = {box.addButton(text(label), QMessageBox.ButtonRole.ActionRole): action for action, label in choices}
        cancel = box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(cancel)
        box.exec()
        return buttons.get(box.clickedButton())

    def commit(self, after=None, all_changes=False):
        if self.blocked or not self.saved() or self.busy:
            return
        service = self.service()
        def prepare(state):
            if any(file.conflicted for file in state.files):
                self.set_feedback(text('resolve_first'))
                return
            staged = any(file.index not in ' ?' for file in state.files)
            stage_all = all_changes or not staged
            if not state.files:
                return
            if stage_all and not self.confirm(text('stage_all_commit')):
                return
            message = self.message.toPlainText().strip() or self.ask('message')
            if not message:
                return
            def work():
                if stage_all:
                    service.run('add', '--all')
                return service.commit(message)
            def complete(_):
                self.message.clear()
                if after:
                    self.guard(after)
            self._pending_refresh = True
            self.job(work, complete)
        self.job(service.status, prepare)

    def preview(self, *_):
        selected = self.selected()
        if not selected or self.busy:
            return
        file, staged = selected[0]
        if not self.blocked and self.controller.check_unsaved_changes() and not self.saved():
            return
        if file.conflicted:
            self.resolve()
            return
        service = self.service()
        project = self.controller.get_current_project()
        project_path = Path(project.path).resolve().relative_to(service.directory).as_posix() if project else None
        def load():
            from proteus.services.git_document import snapshot
            technical = service.diff(file, staged)
            if file.path.lower().endswith(".xml"):
                try:
                    before, after = service.change_content(file, staged)
                    old, new = snapshot(before), snapshot(after)
                    if old or new:
                        roots = None
                        if project_path:
                            roots = (service.document_revision(project_path, 'HEAD' if staged else 'index'),
                                     service.document_revision(project_path, 'index' if staged else 'worktree'))
                        return technical, old, new, roots
                except Exception as error:
                    # Non-PROTEUS XML / invalid XML retain the technical viewer.
                    import logging
                    logging.getLogger(__name__).debug("Document review unavailable: %s", error)
            return technical, None, None
        self.job(load, lambda result: self.present_review(file, staged, result))

    def present_review(self, file, staged, result):
        technical, before, after = result[:3]
        roots = result[3] if len(result) > 3 else None
        if before is None and after is None:
            self.show_output(technical, file.path)
            return
        self._review_names[file.path] = (after or before).name
        from proteus.views.components.git_document_review import GitRenderedReview
        container = getattr(self.window.project_container, 'views_container', None)
        if container is None or roots is None:
            self.show_output(technical, file.path)
            return
        review = GitRenderedReview(self.controller, roots, (after or before).oid, staged,
                                   lambda: self.guard(lambda: self.stage_reviewed_file(file, staged, technical)), container)
        review.stage.setEnabled(not self.blocked)
        # Reopening a file replaces its old snapshot instead of accumulating tabs.
        key = (file.path, staged)
        for index in range(container.count() - 1, -1, -1):
            old_review = container.widget(index)
            if getattr(old_review, 'git_review_key', None) == key:
                container.removeTab(index)
                old_review.deleteLater()
        review.git_review_key = key
        index = container.addTab(review, git_icon('changes', self), (after or before).name + ' · ' + text('comparison_tab'))
        container.setCurrentIndex(index)

    def stage_reviewed_file(self, file, unstage=False, expected_diff=None):
        if self.blocked or not self.saved() or self.busy:
            return
        service = self.service()
        paths = [file.path] + ([file.original] if file.original else [])
        self._pending_refresh = True
        def work():
            if expected_diff is not None and service.diff(file, unstage) != expected_diff:
                raise GitError(text("review_changed"))
            return service.unstage(paths) if unstage else service.stage(paths)
        self.job(work)

    def discard(self):
        selected = self.selected()
        if not selected or not self.saved() or self.busy:
            return
        # Deleting untracked files is intentionally a separate, explicit action.
        if any(file.index == "?" or file.conflicted for file, _ in selected):
            QMessageBox.information(self, text("title"), text("discard_tracked"))
            return
        paths = list(dict.fromkeys(file.path for file, _ in selected))
        if self.confirm(text("discard_confirm") + "\n" + "\n".join(paths)):
            self.command(["restore", "--worktree", "--", *paths], changes_disk=True)

    def initialize(self):
        if self.directory and self.confirm(text("init_confirm") + "\n" + str(self.directory)):
            service = self.service(self.directory)
            self._pending_refresh = True
            self.job(lambda: service.run("init"))

    def clone(self):
        url = self.ask("url")
        if not url:
            return
        destination = QFileDialog.getSaveFileName(self, text("clone_destination"))[0]
        if not destination:
            return
        target = Path(destination)
        if target.exists():
            QMessageBox.warning(self, text("title"), text("destination_exists"))
            return
        service = self.service(target.parent)
        def done(_):
            if (target / "proteus.xml").is_file() and self.saved():
                self.controller.load_project(str(target))
            else:
                self.report_output(str(target), text('clone'))
        self.job(lambda: service.run("clone", "--", url, str(target)), done)

    def choose_branch(self):
        if not self.status or self.busy:
            return
        service = self.service()
        def choose(references):
            from proteus.views.components.git_branches import GitBranchDialog
            picker = GitBranchDialog(references, self.status.branch, self)
            choice = picker.choice if picker.exec() else None
            picker.deleteLater()
            if choice:
                self.guard(lambda: self._branch_choice(service, references, choice))
        self.job(service.references, choose)

    def _branch_choice(self, service, references, choice):
        from proteus.views.components.git_branches import GitBranchDialog
        operation, reference = choice
        if operation == "create":
            self.create_branch()
            return
        new_name = None
        detached = operation == "detach"
        if operation in {"create_from", "detach"} and reference is None:
            picker = GitBranchDialog(references, self.status.branch, self,
                                     mode="source" if operation == "create_from" else "detach")
            choice = picker.choice if picker.exec() else None
            picker.deleteLater()
            if not choice:
                return
            reference = choice[1]
        if operation == "create_from":
            new_name = self.ask("create_branch")
            if not new_name:
                return
        if not new_name and not detached and getattr(reference, 'kind', None) == 'remote':
            locals_ = [ref for ref in references if ref.kind == 'local']
            tracked = next((ref for ref in locals_ if ref.upstream == reference.name), None)
            if tracked:
                reference = tracked
            else:
                remotes = [name for name, _ in self.status.remotes]
                remote_name = next((name for name in sorted(remotes, key=len, reverse=True) if reference.name.startswith(name + '/')), None)
                local_name = reference.name[len(remote_name) + 1:] if remote_name else reference.name.split('/', 1)[-1]
                existing = next((ref for ref in locals_ if ref.name == local_name), None)
                if existing:
                    choice = self.pending_choice('remote_branch_collision', [('new', 'remote_create_named'), ('local', 'remote_use_local')])
                    if choice == 'new':
                        new_name = self.ask('create_branch', local_name + '-local')
                        if not new_name:
                            return
                    elif choice == 'local':
                        reference = existing
                    else:
                        return
        # The picker can remain open while a silent status query finishes.
        if self.busy and self._quiet:
            self._after_refresh = lambda: self._checkout_reference(service, reference, new_name, detached)
        else:
            self._checkout_reference(service, reference, new_name, detached)

    def _checkout_reference(self, service, reference, new_name=None, detached=False):
        if not self.saved():
            return
        full_name = reference.full_name if hasattr(reference, "full_name") else reference
        def work():
            if service.status().files:
                raise GitError(text("clean_first"))
            if new_name:
                return service.create_branch(new_name, full_name, track=getattr(reference, "kind", None) == "remote")
            if detached or getattr(reference, "kind", None) == "tag":
                return service.detach(full_name)
            return service.switch(reference.name, remote_reference=True) if getattr(reference, 'kind', None) == 'remote' else service.switch(reference.name)
        self._pending_refresh = True
        self.job(work, changes_disk=True)

    def create_branch(self):
        branch = self.ask("create_branch")
        if branch and self.saved():
            service = self.service()
            self._pending_refresh = True
            self.job(lambda: service.switch(branch, create=True))

    def rename_branch(self):
        branch = self.ask("rename_branch", self.status.branch)
        if branch:
            self.command(["branch", "-m", "--", branch])

    def pick_reference(self, service, callback, local_only=False):
        def choose(references):
            from proteus.views.components.git_branches import GitBranchDialog
            candidates = [ref for ref in references if (not local_only or ref.kind == 'local')
                          and not (ref.kind == 'local' and ref.name == self.status.branch)]
            if not candidates:
                self.set_feedback(text('no_other_branches'))
                return
            dialog = GitBranchDialog(candidates, self.status.branch, self, mode='source')
            dialog.search.setPlaceholderText(text('delete_branch') if local_only else text('branch_source'))
            accepted = dialog.exec()
            choice = dialog.choice if accepted else None
            dialog.deleteLater()
            if choice:
                self.guard(lambda: callback(choice[1]))
        self.job(service.references, choose)

    def delete_branch(self):
        service = self.service()
        def remove(reference):
            if self.confirm(text('delete_branch') + ': ' + reference.name):
                self.command(['branch', '-d', '--', reference.name])
        self.pick_reference(service, remove, local_only=True)

    def pull(self):
        if not self.status or self.busy or self.blocked or not self.saved():
            return
        strategy = self.pick('pull_strategy', ['Fast-forward', 'Merge', 'Rebase'])
        if not strategy:
            return
        flag = {'Fast-forward': '--ff-only', 'Merge': '--no-rebase', 'Rebase': '--rebase'}[strategy]
        service = self.service()
        def prepare(state):
            if any(file.conflicted for file in state.files):
                self.set_feedback(text('resolve_first'))
                return
            choice = self.pending_choice('pull_pending', [('stash', 'stash_pull'), ('commit', 'commit_pull')]) if state.files else 'clean'
            if choice == 'commit':
                self.commit(lambda: self.command(['pull', flag], changes_disk=True, require_clean=True), all_changes=True)
            elif choice == 'stash':
                self._pending_refresh = True
                self.job(lambda: service.pull_with_stash(flag, text('stash_retained')), changes_disk=True)
            elif choice == 'clean':
                self.command(['pull', flag], changes_disk=True, require_clean=True)
        self.job(service.status, prepare)

    def push(self):
        if not self.status or self.busy:
            return
        service = self.service()
        def prepare(result):
            state, has_commits = result
            if not has_commits:
                QMessageBox.information(self, text('push'), text('push_first_commit'))
                return
            self.status = state
            if not state.upstream:
                if not state.remotes:
                    QMessageBox.information(self, text('push'), text('configure_remote_first'))
                    return
                self.publish()
                return
            def complete(output):
                updates = [line for line in output.splitlines() if len(line) > 1 and line[1] == '\t']
                if updates and all(line.startswith('=') for line in updates):
                    message = text('push_nothing')
                    if state.files:
                        message += '\n\n' + text('push_uncommitted')
                    self.set_feedback(message)
                    QMessageBox.information(self, text('push'), message)
                elif output.strip():
                    self.report_output(output, text('push'))
            self._pending_refresh = True
            self.job(lambda: service.run('push', '--porcelain'), complete)
        self.job(lambda: (state := service.status(), state.has_commits), prepare)

    def publish(self):
        if not self.status or self.busy or not self.status.has_commits or not self.status.remotes or self.status.upstream or self.status.branch.startswith("HEAD "):
            return
        service = self.service()
        def choose(remotes):
            remote = self.pick("remotes", remotes)
            if remote:
                self._pending_refresh = True
                self.job(lambda: service.publish(remote), lambda output: self.report_output(output, text('publish_branch')))
        self.job(service.remote_names, choose)

    def remotes(self):
        if not self.status:
            return
        from proteus.views.components.git_remotes import GitRemotesDialog
        dialog = GitRemotesDialog(self.status.remotes, self)
        dialog.exec()
        command = dialog.command
        dialog.deleteLater()
        if command and (command[1] != 'remove' or self.confirm(text('remove_remote') + ': ' + command[-1])):
            self.command(command)

    def identity(self):
        name = self.ask("user_name")
        email = self.ask("user_email") if name else None
        if email:
            service = self.service()
            self.job(lambda: (service.run("config", "--local", "user.name", name),
                              service.run("config", "--local", "user.email", email)))

    def history(self):
        from proteus.views.components.git_history import GitHistoryDialog
        service = self.service()
        self.job(service.history, lambda commits: GitHistoryDialog(service, commits, self).exec())

    def integrate(self, operation):
        service = self.service()
        def apply(reference):
            if not self.confirm(text(operation) + ': ' + reference.name + '\n' + text('confirm_operation')):
                return
            args = [operation, '--no-edit', reference.full_name] if operation == 'merge' else [operation, reference.full_name]
            self.command(args, changes_disk=True, require_clean=True)
        self.pick_reference(service, apply)

    def continue_operation(self):
        operation = self.status.operation
        if operation:
            args = ["commit", "--no-edit"] if operation == "merge" else [operation, "--continue"]
            self.command(args, changes_disk=True)

    def abort_operation(self):
        if self.status.operation and self.confirm(text("abort_confirm")):
            self.command([self.status.operation, "--abort"], changes_disk=True)

    def stash(self):
        if not self.status or self.busy or self.blocked or not self.status.files or not self.saved():
            return
        service = self.service()
        def work():
            return service.run('stash', 'push', '--include-untracked') if service.status().files else ''
        self._pending_refresh = True
        self.job(work, changes_disk=True)

    def apply_stash(self):
        if not self.status or self.busy:
            return
        service = self.service()
        def choose(output):
            if not output.strip():
                self.set_feedback(text('no_stashes'))
                return
            stash = self.pick("apply_stash", output.splitlines())
            if stash:
                self.command(["stash", "apply", stash.split(":", 1)[0]], changes_disk=True, require_clean=True)
        self.job(lambda: service.run("stash", "list"), choose)

    def commit_action(self, operation):
        commit = self.ask("commit_reference")
        if commit and not commit.startswith("-") and self.confirm(text("confirm_operation") + "\n" + operation + " " + commit):
            self.command([operation, "--no-edit", commit], changes_disk=True, require_clean=True)

    def tag(self):
        tag = self.ask("tag")
        if tag:
            self.command(["tag", "--", tag])

    def publish_github(self):
        # Keep provider authentication outside PROTEUS; gh owns its token store.
        import shutil
        import subprocess
        executable = shutil.which("gh")
        if not executable:
            QMessageBox.information(self, text("title"), text("github_browser"))
            QDesktopServices.openUrl(QUrl("https://github.com/new"))
            return
        name = self.ask("github_name")
        visibility = self.pick("visibility", ["private", "public"]) if name else None
        if name and (name.startswith("-") or any(c.isspace() for c in name)):
            return
        if visibility and self.confirm(text("publish_confirm") + "\n" + name + " (" + visibility + ")"):
            root = self.status.root
            def work():
                if "origin" in GitService(root, self.git_executable, self.trusted_root).remote_names():
                    raise GitError(text("origin_exists"))
                result = subprocess.run([executable, "repo", "create", name, "--" + visibility,
                                         "--source", str(root), "--remote", "origin", "--push"],
                                        cwd=root, capture_output=True, timeout=120,
                                        creationflags=subprocess.CREATE_NO_WINDOW if __import__("os").name == "nt" else 0)
                if result.returncode:
                    raise GitError(result.stderr.decode("utf-8", errors="replace"))
                return result.stdout.decode("utf-8", errors="replace")
            self._pending_refresh = True
            self.job(work, self.show_output)

    def reload(self):
        if self.directory and not self.busy and self.saved():
            self.job(lambda: None, changes_disk=True)

    def resolve(self):
        selected = self.selected()
        if not selected or not selected[0][0].conflicted or self.busy:
            return
        file = selected[0][0]
        service = self.service()
        def versions():
            return [service.run("show", f":{stage}:{file.path}", check=False) for stage in (1, 2, 3)]
        def edit(contents):
            dialog = QDialog(self)
            dialog.setWindowTitle(file.path)
            dialog.resize(1000, 700)
            layout = QVBoxLayout(dialog)
            from PyQt6.QtWidgets import QTabWidget
            tabs = QTabWidget()
            for key, content in zip(("base", "ours", "theirs"), contents):
                view = QPlainTextEdit()
                view.setReadOnly(True)
                view.setPlainText(content)
                tabs.addTab(view, text(key))
            layout.addWidget(tabs)
            layout.addWidget(QLabel(text("resolution")))
            editor = QPlainTextEdit()
            path = service.directory / file.path
            original_bytes = path.read_bytes() if path.exists() else None
            editor.setPlainText(original_bytes.decode("utf-8", errors="replace") if original_bytes else "")
            layout.addWidget(editor)
            save = QPushButton(text("resolve_save"))
            delete = QPushButton(text("resolve_delete"))
            layout.addWidget(save)
            layout.addWidget(delete)
            def finish(remove=False):
                content = editor.toPlainText()
                try:
                    if not remove and path.suffix.lower() == ".xml":
                        from lxml import etree
                        etree.fromstring(content.encode("utf-8"), etree.XMLParser(resolve_entities=False, no_network=True))
                    if any(marker in content for marker in ("<<<<<<<", "=======", ">>>>>>>")) and not remove:
                        raise GitError(text("resolve_first"))
                    if not self.confirm(text("resolve_delete") if remove else text("resolve_save")):
                        return
                except Exception as error:
                    QMessageBox.warning(dialog, text("title"), str(error))
                    return
                dialog.accept()
                def work():
                    # Refuse to overwrite an externally changed resolution.
                    current = path.read_bytes() if path.exists() else None
                    if current != original_bytes:
                        raise GitError(text("external_changes"))
                    if path.is_symlink() or not path.resolve().is_relative_to(service.directory.resolve()):
                        raise GitError("Cannot edit a conflict through a symbolic link.")
                    if remove:
                        return service.run("rm", "--", file.path)
                    path.write_text(content, encoding="utf-8")
                    return service.stage([file.path])
                self._pending_refresh = True
                self.job(work, changes_disk=True)
            save.clicked.connect(lambda: finish(False))
            delete.clicked.connect(lambda: finish(True))
            dialog.exec()
        self.job(versions, edit)

    def stage_all(self):
        if self.blocked or not self.saved() or self.busy:
            return
        service = self.service()
        self._pending_refresh = True
        def work():
            paths = [file.path for file in service.status().files if file.worktree != ' ']
            return service.stage(paths) if paths else ''
        self.job(work)

    def unstage_all(self):
        service = self.service()
        self._pending_refresh = True
        def work():
            paths = list(dict.fromkeys(path for file in service.status().files if file.index not in " ?"
                                       for path in (file.path, file.original) if path))
            return service.unstage(paths) if paths else ""
        self.job(work)

    def stage_hunk(self):
        selected = self.selected()
        if not selected or self.blocked or not self.saved() or self.busy:
            return
        file, staged = selected[0]
        if staged:
            return
        service = self.service()
        def choose(patches):
            dialog = QDialog(self)
            dialog.setWindowTitle(text("stage_hunk"))
            dialog.resize(850, 600)
            layout = QVBoxLayout(dialog)
            from PyQt6.QtWidgets import QComboBox
            choices = QComboBox()
            choices.addItems([str(i + 1) for i in range(len(patches))])
            preview = QPlainTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(patches[0])
            choices.currentIndexChanged.connect(lambda i: preview.setPlainText(patches[i]))
            layout.addWidget(choices)
            layout.addWidget(preview)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec():
                patch = patches[choices.currentIndex()]
                self._pending_refresh = True
                self.job(lambda: service.stage_hunk(patch))
        self.job(lambda: service.hunks(file), choose)

    def ignore(self):
        paths = [file.path for file, _ in self.selected() if file.index == "?"]
        if not paths or not self.confirm(text("ignore") + "\n" + "\n".join(paths)):
            return
        root = self.status.root
        def work():
            def pattern(path):
                # Gitignore wildcards and backslashes must match literally.
                for char in ("\\", "*", "?", "[", "]", " "):
                    path = path.replace(char, "\\" + char)
                return "/" + path
            with (root / ".gitignore").open("a", encoding="utf-8", newline="\n") as target:
                target.write("\n" + "\n".join(pattern(path) for path in paths) + "\n")
        self._pending_refresh = True
        self.job(work)

    def worktrees(self):
        from proteus.views.components.git_worktrees import GitWorktreesDialog
        service = self.service()
        def show(entries):
            dialog = GitWorktreesDialog(entries, service.directory, self,
                                        can_create=self.actions['add_worktree'].isEnabled())
            dialog.exec()
            create = dialog.action == 'create'
            dialog.deleteLater()
            if create:
                self.guard(self.add_worktree)
        self.job(service.worktrees, show)

    def add_worktree(self):
        branch = self.ask("create_branch")
        destination = QFileDialog.getSaveFileName(self, text("clone_destination"))[0] if branch else None
        if destination:
            service = self.service()
            def work():
                service.run("check-ref-format", "--branch", branch)
                return service.run("worktree", "add", "-b", branch, "--", destination)
            self.job(work, lambda output: self.report_output(output, text('add_worktree')))

    def trust_repository(self):
        folder = QFileDialog.getExistingDirectory(self, text("trust"), str(self.directory or Path.cwd()))
        if not folder:
            return
        root = Path(folder).resolve()
        if not (root / ".git").exists():
            raise GitError(text("choose_root"))
        if self.confirm(text("trust_confirm") + "\n" + str(root)):
            # Trust only this explicit path for this session. Never disable
            # ownership checks globally or persist a wildcard exception.
            self.trusted_root = root
            self.refresh()

    def set_git_path(self):
        path = QFileDialog.getOpenFileName(self, text("git_path"))[0]
        if path:
            service = GitService(self.directory or Path.cwd(), path)
            if not service.run("--version").startswith("git version "):
                raise GitError("Choose a Git executable.")
            settings = Config().app_settings
            if not settings.config_parser.has_section("git"):
                settings.config_parser.add_section("git")
            settings.config_parser.set("git", "executable", path)
            settings.save()
            self.git_executable = path
            self.refresh()
