"""Document-level review of stored PROTEUS objects, independent of XML layout."""
from dataclasses import dataclass
from difflib import SequenceMatcher
from html import escape
import re
from lxml import etree


@dataclass(frozen=True)
class ObjectSnapshot:
    oid: str
    name: str
    properties: dict[str, str]
    children: tuple[str, ...]
    attributes: dict[str, str]
    metadata: dict[str, dict[str, str]]


def snapshot(source: str | None) -> ObjectSnapshot | None:
    if source is None:
        return None
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(source.encode('utf-8'), parser)
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError('XML entity references are not supported in document reviews.')
    if root.tag not in {'object', 'project'} or not root.get('id'):
        raise ValueError('Not a PROTEUS document object.')
    properties = {}
    metadata = {}
    for element in root.findall('./properties/*'):
        name = element.get('name', '')
        if element.tag == 'traceProperty':
            value = '\n'.join(child.get('target', '') for child in element)
        elif element.tag == 'codeProperty':
            value = ''.join((child.text or '') for child in element)
        elif len(element):
            value = '\n'.join(''.join(child.itertext()).strip() or child.get('target', '') or child.get('name', '') for child in element)
        else:
            value = element.text or ''
        properties[name] = value
        metadata[name] = {'type': element.tag, **{key: value for key, value in element.attrib.items() if key != 'name'}}
    children = tuple(child.get('id', '') for child in root.findall('./children/child'))
    if root.tag == 'project':
        children = tuple(child.get('id', '') for child in root.findall('./documents/*'))
    return ObjectSnapshot(root.get('id', ''), properties.get(':Proteus-name', ''), properties,
                          children, {key: value for key, value in root.attrib.items() if key != 'id'}, metadata)


def highlighted_words(before: str, after: str):
    left = re.findall(r'\s+|\S+', before)
    right = re.findall(r'\s+|\S+', after)
    old, new = [], []
    # Avoid pathological quadratic work in very large rich-text properties.
    if len(left) + len(right) > 10000:
        return escape(before).replace('\n', '<br>'), escape(after).replace('\n', '<br>')
    for operation, a, b, c, d in SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        old_text = escape(''.join(left[a:b])).replace('\n', '<br>')
        new_text = escape(''.join(right[c:d])).replace('\n', '<br>')
        old.append(f'<span style="background-color:#fbe2e4;color:#7f2533;text-decoration:line-through">{old_text}</span>' if operation in {'delete','replace'} else old_text)
        new.append(f'<span style="background-color:#d9efdf;color:#185d35">{new_text}</span>' if operation in {'insert','replace'} else new_text)
    return ''.join(old), ''.join(new)


def review_html(before, after, label, names, strings):
    """Escape all document content; never execute document markup or plugins."""
    title = (after or before).name
    rows = []
    old_properties, new_properties = before.properties if before else {}, after.properties if after else {}
    for key in dict.fromkeys([*old_properties, *new_properties]):
        old, new = old_properties.get(key, ''), new_properties.get(key, '')
        old_meta = before.metadata.get(key, {}) if before else {}
        new_meta = after.metadata.get(key, {}) if after else {}
        if before and after and old == new and old_meta == new_meta:
            continue
        old = '\n'.join(names.get(line, line) for line in old.split('\n'))
        new = '\n'.join(names.get(line, line) for line in new.split('\n'))
        if before and after and old_meta != new_meta:
            old += '\n' + strings['property_settings'] + ': ' + ', '.join(f'{k}={v}' for k, v in old_meta.items())
            new += '\n' + strings['property_settings'] + ': ' + ', '.join(f'{k}={v}' for k, v in new_meta.items())
        old, new = highlighted_words(old, new)
        rows.append(f'<h3>{escape(label(key))}</h3><table width="100%" cellspacing="8"><tr><td width="50%" valign="top">{old or "—"}</td><td width="50%" valign="top">{new or "—"}</td></tr></table>')
    old_children, new_children = before.children if before else (), after.children if after else ()
    if old_children != new_children:
        old, new = highlighted_words('\n'.join(names.get(oid, oid) for oid in old_children), '\n'.join(names.get(oid, oid) for oid in new_children))
        rows.append(f'<h3>{escape(strings["structure"])}</h3><table width="100%"><tr><td width="50%">{old or "—"}</td><td width="50%">{new or "—"}</td></tr></table>')
    if before and after:
        for key in dict.fromkeys([*before.attributes, *after.attributes]):
            old, new = before.attributes.get(key, ''), after.attributes.get(key, '')
            if old != new:
                old, new = highlighted_words(old, new)
                rows.append(f'<h3>{escape(label(key))}</h3><table width="100%"><tr><td width="50%">{old or "—"}</td><td width="50%">{new or "—"}</td></tr></table>')
    body = ''.join(rows) or f'<p>{escape(strings["no_content_change"])}</p>'
    return f'<h2>{escape(title)}</h2><p>{escape(strings["comparison"])}</p><table width="100%"><tr><th width="50%" align="left">{escape(strings["before"])}</th><th width="50%" align="left">{escape(strings["after"])}</th></tr></table>{body}'


def assemble_project(project_source, objects):
    """Expand stored references using only files from the same Git snapshot."""
    from copy import deepcopy
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(project_source.encode('utf-8'), parser)
    parsed = {}
    for source in objects:
        node = etree.fromstring(source.encode('utf-8'), parser)
        if node.tag == 'object':
            parsed[node.get('id')] = node
    def expand(node, ancestors):
        for ref in list(node.xpath('./documents/document | ./children/child')):
            oid = ref.get('id')
            if oid in ancestors:
                raise ValueError('Cyclic document structure')
            if oid not in parsed:
                ref.getparent().remove(ref)
                continue
            child = deepcopy(parsed[oid])
            expand(child, ancestors | {oid})
            ref.getparent().replace(ref, child)
    expand(root, set())
    return root
