"""Semantic reviews and reversible rendering annotations."""
from PyQt6.QtQml import QJSEngine
from proteus.services.git_document import snapshot, review_html
from proteus.views.components.git_document_review import document_highlight_script


BEFORE = '<object id="paragraph" classes="paragraph"><properties><stringProperty name=":Proteus-name">Introduction</stringProperty><markdownProperty name="text">The old sentence.</markdownProperty></properties><children/></object>'
AFTER = BEFORE.replace('old', 'new')
STRINGS = {key: key for key in ('structure', 'no_content_change', 'comparison', 'before', 'after', 'property_settings')}


def test_review_marks_content_words_instead_of_xml_tags():
    before, after = snapshot(BEFORE), snapshot(AFTER)
    html = review_html(before, after, lambda key: key, {}, STRINGS)
    assert 'Introduction' in html
    assert 'old' in html and 'new' in html
    assert 'text-decoration:line-through' in html
    assert '<object' not in html and 'markdownProperty' not in html


def test_review_ignores_xml_formatting_but_reports_property_metadata():
    before = snapshot(BEFORE)
    formatted = BEFORE.replace('><', '>\n  <')
    assert 'no_content_change' in review_html(before, snapshot(formatted), str, {}, STRINGS)
    changed = BEFORE.replace('name="text"', 'name="text" required="true"')
    assert 'required=true' in review_html(before, snapshot(changed), str, {}, STRINGS)


def test_review_escapes_markup_and_displays_added_and_deleted_content():
    source = AFTER.replace('The new sentence.', '&lt;script&gt;alert(1)&lt;/script&gt;')
    added = review_html(None, snapshot(source), str, {}, STRINGS)
    assert '<script>' not in added
    assert '&lt;script&gt;' in added
    assert 'Introduction' in review_html(snapshot(BEFORE), None, str, {}, STRINGS)


def test_highlighting_is_reversible_and_does_not_modify_document_text(qapp):
    engine = QJSEngine()
    setup = r'''var nodes = {};
      function node(id) { return {id, attrs:{}, textContent:'Original document',
        setAttribute(k,v){this.attrs[k]=v;}, removeAttribute(k){delete this.attrs[k];},
        getAttribute(k){return this.attrs[k];}}; }
      nodes.paragraph = node('paragraph'); nodes.unchanged = node('unchanged');
      var document = {getElementById(id){return nodes[id] || null;},
        createElement(){return node('');},
        head:{appendChild(el){nodes[el.id]=el;}},
        querySelectorAll(selector){return Object.values(nodes).filter(el => selector === '[data-proteus-git-change]' ? el.attrs['data-proteus-git-change'] : el.attrs['data-proteus-id']);}};'''
    assert not engine.evaluate(setup).isError()
    result = engine.evaluate(document_highlight_script({'paragraph': 'modified'}))
    assert not result.isError(), result.toString()
    assert engine.evaluate("nodes.paragraph.attrs['data-proteus-git-change']").toString() == 'modified'
    assert engine.evaluate('nodes.paragraph.textContent').toString() == 'Original document'
    assert engine.evaluate("nodes.unchanged.attrs['data-proteus-git-change']").isUndefined()
    engine.evaluate(document_highlight_script({}))
    assert engine.evaluate("nodes.paragraph.attrs['data-proteus-git-change']").isUndefined()


def test_snapshot_does_not_resolve_external_entities(tmp_path):
    secret = tmp_path / 'secret.txt'
    secret.write_text('DO NOT READ THIS FILE')
    source = '<!DOCTYPE object [<!ENTITY secret SYSTEM "' + secret.as_uri() + '">]><object id="one"><properties><stringProperty name=":Proteus-name">&secret;</stringProperty></properties><children/></object>'
    import pytest
    with pytest.raises(ValueError, match='entity references'):
        snapshot(source)


def test_assembled_snapshot_rejects_cycles_and_preserves_input():
    import pytest
    from proteus.services.git_document import assemble_project
    project = '<project id="p"><properties/><documents><document id="one"/></documents></project>'
    child = '<object id="one"><properties/><children><child id="one"/></children></object>'
    with pytest.raises(ValueError, match='Cyclic'):
        assemble_project(project, [child])
    assert '<document id="one"/>' in project
