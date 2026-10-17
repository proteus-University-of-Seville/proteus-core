"""User-facing content review and reversible highlights in rendered documents."""
import json
from PyQt6 import sip
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from proteus.application.resources.translator import translate as _
from proteus.views.components.git_icons import git_icon


def text(key):
    return _('git.' + key)


def document_highlight_script(changes):
    return r'''(() => {
      let style = document.getElementById('proteus-git-review-style');
      if (!style) {
        style = document.createElement('style'); style.id = 'proteus-git-review-style';
        style.textContent = '[data-proteus-git-change] { box-shadow: inset 3px 0 #b89443; background-color: rgba(184,148,67,.10); }'
          + '[data-proteus-git-change="added"] { box-shadow: inset 3px 0 #57886a; background-color: rgba(87,136,106,.09); }'
          + '@media print { [data-proteus-git-change] { box-shadow: none !important; background-color: transparent !important; } }';
        (document.head || document.documentElement).appendChild(style);
      }
      document.querySelectorAll('[data-proteus-git-change]').forEach(el => el.removeAttribute('data-proteus-git-change'));
      const changes = __CHANGES__;
      Object.entries(changes).forEach(([id, kind]) => {
        const el = document.getElementById(id) || Array.from(document.querySelectorAll('[data-proteus-id]')).find(node => node.getAttribute('data-proteus-id') === id);
        if (el) el.setAttribute('data-proteus-git-change', kind);
      });
    })();'''.replace('__CHANGES__', json.dumps(changes, ensure_ascii=True))


class GitRenderedReview(QWidget):
    """Disposable, read-only comparison tab using the active document template."""
    def __init__(self, controller, roots, oid, staged, stage_action, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QLabel, QSplitter, QSizePolicy
        from PyQt6.QtCore import Qt, QUrl, QTemporaryDir
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEnginePage
        from proteus.application.configuration.config import Config
        from proteus.application.state.manager import StateManager
        from proteus.application import TEMPLATE_DUMMY_SEARCH_PATH, replace_assets_urls
        from proteus.model import ASSETS_REPOSITORY
        from html import escape
        from pathlib import Path
        self._html_directory = QTemporaryDir()
        if not self._html_directory.isValid():
            raise OSError('Cannot create temporary document comparison')
        self.destroyed.connect(lambda _=None, folder=self._html_directory: folder.remove())
        layout = QVBoxLayout(self)
        tools = QHBoxLayout()
        tools.addStretch()
        self.stage = QPushButton(text('unstage_object' if staged else 'stage_object'))
        self.stage.setIcon(git_icon('unstage' if staged else 'stage', self))
        self.stage.clicked.connect(stage_action)
        tools.addWidget(self.stage)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.addLayout(tools, 0)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split, 1)
        self.browsers = []
        self._rendered_text = {}
        self._review_oid = oid
        state = StateManager()
        view = state.get_current_view() or Config().app_settings.default_view
        self.template = view
        for index, root in enumerate(roots):
            column = QWidget()
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(0, 0, 0, 0)
            label = text(('last_commit' if staged else 'prepared_version') if index == 0 else ('prepared_version' if staged else 'saved_document'))
            heading = QLabel(label)
            heading.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            heading.setObjectName('gitComparisonHeading')
            title_font = heading.font()
            title_font.setBold(True)
            if title_font.pointSizeF() > 0:
                title_font.setPointSizeF(title_font.pointSizeF() + 1)
            heading.setFont(title_font)
            heading.setContentsMargins(12, 10, 12, 10)
            heading.setStyleSheet(
                'QLabel#gitComparisonHeading {'
                ' color: palette(window-text); background-color: palette(alternate-base);'
                ' border: none; border-bottom: 1px solid palette(mid); }'
            )
            column_layout.setSpacing(0)
            column_layout.addWidget(heading, 0)
            browser = QWebEngineView(column)
            class ReviewPage(QWebEnginePage):
                def acceptNavigationRequest(self, url, navigation_type, main_frame):
                    return navigation_type != QWebEnginePage.NavigationType.NavigationTypeLinkClicked
                def javaScriptConsoleMessage(self, level, message, line, source):
                    pass
            browser.setPage(ReviewPage(browser))
            browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            column_layout.addWidget(browser, 1)
            split.addWidget(column)
            self.browsers.append(browser)
            target = root.xpath('descendant-or-self::*[@id=$oid]', oid=oid) if root is not None else []
            if not target:
                self._rendered_text[index] = ''
                browser.setHtml('<p>' + escape(text('version_absent')) + '</p>')
                continue
            target = target[0]
            documents = root.xpath('./documents/object')
            document = next((doc for doc in documents if doc is target or doc in target.iterancestors()), None)
            previous_document = state.current_document
            try:
                # The template extension reads this value synchronously. No events or model edits.
                if document is not None:
                    state.current_document = document.get('id')
                html = controller._render_service.render(root, view)
            finally:
                state.current_document = previous_document
            assets = (state.current_project_path / ASSETS_REPOSITORY).as_posix()
            html = replace_assets_urls(html, 'file:///' + assets + '/')
            xslt = Config().profile_settings.xslt_directory.as_posix()
            html = html.replace(TEMPLATE_DUMMY_SEARCH_PATH + ':///', 'file:///' + xslt + '/')
            # Keep the target's ancestors (layout/styles) and remove unrelated siblings visually.
            script = """(() => {
                const target = document.getElementById(__ID__);
                if (!target) return;
                let node = target;
                while (node.parentElement && node !== document.body) {
                    for (const sibling of node.parentElement.children) {
                        if (sibling !== node && !['STYLE','LINK','SCRIPT'].includes(sibling.tagName)) sibling.style.display = 'none';
                    }
                    node = node.parentElement;
                }
                document.body.style.margin = '12px';
                for (let parent = target.parentElement; parent; parent = parent.parentElement) {
                    parent.style.minHeight = '0'; parent.style.height = 'auto';
                    parent.style.minWidth = '0'; parent.style.width = 'auto';
                    parent.style.maxWidth = '100%'; parent.style.boxSizing = 'border-box';
                    if (parent !== document.body && parent !== document.documentElement) {
                        parent.style.margin = '0'; parent.style.padding = '0';
                    }
                }
                target.style.marginTop = '0';
                target.style.maxWidth = '100%'; target.style.minWidth = '0';
                target.style.overflowWrap = 'anywhere';
                target.style.boxSizing = 'border-box';
                window.scrollTo(0, 0);
            })();""".replace('__ID__', json.dumps(oid))
            browser.loadFinished.connect(lambda ok, browser=browser, script=script, index=index:
                self._loaded(browser, index, script) if ok else None)
            # setHtml sends content through a data URL with a 2 MB Chromium limit.
            # A local temporary file supports large documents and lives only with this tab.
            from lxml import html as html_parser
            document_html = html_parser.document_fromstring(html)
            head = document_html.find('head')
            if head is None:
                head = html_parser.Element('head')
                document_html.insert(0, head)
            base = html_parser.Element('base', href=QUrl.fromLocalFile(str(state.current_project_path) + '/').toString())
            head.insert(0, base)
            path = Path(self._html_directory.path()) / f'{index}.html'
            path.write_text(html_parser.tostring(document_html, encoding='unicode', method='html'), encoding='utf-8')
            browser.load(QUrl.fromLocalFile(str(path)))
        split.setSizes([500, 500])


    def _loaded(self, browser, index, script):
        if sip.isdeleted(self) or sip.isdeleted(browser):
            return
        browser.page().runJavaScript(script)
        source = """(() => {
            const root = document.getElementById(__ID__) || document.body;
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            let node, text = '';
            while (node = walker.nextNode()) {
                if (!node.parentElement.closest('script,style')) text += node.textContent;
            }
            return text;
        })()""".replace('__ID__', json.dumps(self._review_oid))
        browser.page().runJavaScript(source, lambda value: self._received_text(index, value))

    def _received_text(self, index, value):
        if sip.isdeleted(self) or any(sip.isdeleted(browser) for browser in self.browsers):
            return
        from difflib import SequenceMatcher
        import re
        self._rendered_text[index] = value or ''
        if len(self._rendered_text) != 2:
            return
        # Bound comparison cost for large objects. The two rendered views remain usable.
        tokens = [list(re.finditer(r'\s+|\S+', self._rendered_text[i])) for i in (0, 1)]
        if sum(map(len, tokens)) > 10000:
            return
        ranges = [[], []]
        for op, a, b, c, d in SequenceMatcher(None, [t.group() for t in tokens[0]], [t.group() for t in tokens[1]], autojunk=False).get_opcodes():
            if op == 'equal':
                continue
            for side, start, end in ((0, a, b), (1, c, d)):
                if start < end:
                    # JavaScript text offsets count UTF-16 code units.
                    text_value = self._rendered_text[side]
                    offset = lambda n: len(text_value[:n].encode('utf-16-le')) // 2
                    ranges[side].append([offset(tokens[side][start].start()), offset(tokens[side][end-1].end())])
        for side, browser in enumerate(self.browsers):
            script = """(() => {
                const root = document.getElementById(__ID__) || document.body;
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
                const nodes = []; let node, offset = 0;
                while (node = walker.nextNode()) {
                    if (node.parentElement.closest('script,style')) continue;
                    nodes.push([node, offset]); offset += node.length;
                }
                for (const [node, start] of nodes) {
                    for (const [a,b] of __RANGES__.slice().reverse()) {
                        const left = Math.max(0, a-start), right = Math.min(node.length, b-start);
                        if (left >= right) continue;
                        if (right < node.length) node.splitText(right);
                        const changed = left ? node.splitText(left) : node;
                        const mark = document.createElement('mark');
                        mark.style.backgroundColor = '__COLOR__'; mark.style.color = 'inherit';
                        changed.parentNode.insertBefore(mark, changed); mark.appendChild(changed);
                    }
                }
            })();""".replace('__ID__', json.dumps(self._review_oid)).replace('__RANGES__', json.dumps(ranges[side])).replace('__COLOR__', '#f9d9dc' if side == 0 else '#d9efdf')
            browser.page().runJavaScript(script)
