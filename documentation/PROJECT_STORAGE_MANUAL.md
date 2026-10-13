# Proteus Project Storage Manual

This note summarizes how Proteus stores project data on disk. It is based on the runtime model in the code and on the XML archetypes shipped in `profiles/basic`.

## Overview

Proteus stores project content as XML files inside a project directory.

- The project itself is stored in `proteus.xml`.
- Documents and normal objects are stored as separate XML files in the `objects/` directory.
- Binary or linked assets used by `fileProperty` values live in `assets/`.
- A separate YAML file, `state.yaml`, stores UI state such as the selected document, selected objects, expanded tree nodes, and opened views.

In other words, the content model is XML-based, while the application state is YAML-based.

## Typical Project Layout

```text
my-project/
  proteus.xml
  objects/
    empty-doc.xml
    section-1.xml
    paragraph-1.xml
    stakeholder-1.xml
  assets/
    us-logo.jpg
  state.yaml
  .gitignore
```

Notes:

- The YAML state file is always named `state.yaml` (`STATE_FILE_NAME` in `proteus/application/state`). It is not part of the content and can be deleted safely: the tree is then shown collapsed the next time the project is opened.
- New projects include a `.gitignore` that excludes `state.yaml` and `state.yml`, so that projects can be versioned without UI state.
- The runtime model uses `proteus.xml` as the project file name and `objects/` and `assets/` as the content directories (`PROJECT_FILE_NAME`, `OBJECTS_REPOSITORY` and `ASSETS_REPOSITORY` in `proteus/model/__init__.py`).

## How Projects Are Stored

At runtime, a Proteus project is a directory containing a `proteus.xml` file. The project XML stores:

- The project identifier.
- Project-level properties.
- A list of document IDs.

The documents themselves are not embedded in `proteus.xml`. The file only references them by ID.

Example:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<project id="BASIC">
  <properties>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[BASIC]]></stringProperty>
    <stringProperty name="version" category="general"><![CDATA[1.0]]></stringProperty>
    <dateProperty name=":Proteus-date" category="general">2024-09-17</dateProperty>
    <markdownProperty name="description" category="detail"><![CDATA[]]></markdownProperty>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
  <documents>
    <document id="empty-doc"/>
  </documents>
</project>
```

Important consequence:

- `proteus.xml` is the index of the project.
- Each referenced document must exist as `objects/<document-id>.xml`.
- The order of the `<document>` elements is the order of the documents in the application.

## Project and Document Archetypes

Profiles ship project and document archetypes with almost the same layout, under
`<profile>/archetypes/<language>/`:

```text
projects/<archetype-name>/
  project.xml          same format as proteus.xml, but with a different file name
  objects/
  assets/
  .gitignore
documents/<archetype-name>/
  document.xml         pointer to the document object: <document id="empty-doc"/>
  objects/
    empty-doc.xml      the document object and all its descendants
  assets/
```

When a project is created from a project archetype, Proteus copies the whole directory and
renames `project.xml` to `proteus.xml`. When a document is created from a document
archetype, its objects are cloned into the project (with new IDs, see below) and the
assets they reference are copied into the project's `assets/` directory.

## How Documents Are Stored

In storage terms, a document is just a Proteus object whose `classes` attribute contains `:Proteus-document`.

That means documents are saved exactly like other objects: one XML file per document in `objects/`.

Example document object:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<object
  id="empty-doc"
  classes=":Proteus-document"
  acceptedChildren=":Proteus-any"
>
  <properties>
    <stringProperty name=":Proteus-acronym" category="general"><![CDATA[DOC]]></stringProperty>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[Empty document]]></stringProperty>
    <stringProperty name="version" category="general"><![CDATA[1.0]]></stringProperty>
    <dateProperty name=":Proteus-date" category="general">2024-09-17</dateProperty>
    <markdownProperty name="description" category="detail"><![CDATA[Empty document that can be used as template.]]></markdownProperty>
    <traceProperty name="prepared-for" category="dependencies" acceptedTargets="organization" traceType=":Proteus-dependency"/>
    <traceProperty name="prepared-by" category="dependencies" acceptedTargets="organization" traceType=":Proteus-author"/>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
</object>
```

The project file points to this document by ID:

```xml
<documents>
  <document id="empty-doc"/>
</documents>
```

## How Objects Are Stored

Every non-project element is stored as an XML file in `objects/` named after its ID:

```text
objects/<id>.xml
```

The object ID must match the XML file name exactly. For example, an object stored in `objects/stakeholder-1.xml` must have `id="stakeholder-1"` in its root `<object>` element.

Proteus resolves objects by building the file path from the ID, so this naming rule is mandatory. By default, when Proteus clones or creates objects programmatically, it generates 12-character short UUIDs for new IDs. If an object file is created manually, any string can be used as the object ID as long as:

- the root `<object>` uses that same string in its `id` attribute
- the file is stored as `objects/<that-same-id>.xml`

An object file stores:

- `id`: the object identifier.
- `classes`: one or more class tags, from the most general to the most specific. The last one is the *main class* of the object: it selects its icon, its label in the toolbar and in the rendered document, and the CSS class of its table.
- `acceptedChildren`: which child classes are allowed.
- `acceptedParents`: which parents are allowed.
- `selectedCategory`: optional UI hint for the preferred property category.
- `<properties>`: the object's properties.
- `<children>`: references to child object IDs. With `numbered="true"`, the children are numbered when they are displayed.

Attribute rules for parent/child constraints:

- `id`, `classes` and `acceptedChildren` are mandatory in `<object>`: a file without any of them cannot be loaded.
- `acceptedChildren` can be `:Proteus-any` (accept any child class), `:Proteus-none` (leaf object), or one or more specific class names.
- `acceptedParents` is optional.
- If `acceptedParents` is omitted, its default behavior is `:Proteus-any`.
- A child is accepted only if the parent's `acceptedChildren` contains `:Proteus-any` or one of the child's classes, **and** the child's `acceptedParents` contains `:Proteus-any` or one of the parent's classes. Class tags may be *abstract*: tags shared by several archetypes (e.g. `use-case-step`) that have no archetype of their own.

Files written by Proteus are normalized: they always include `acceptedParents`, a `category` attribute on every property and a `<children>` element (empty for leaves), and start with `<?xml version='1.0' encoding='UTF-8'?>`. Archetype files in profiles are written by hand and often omit optional attributes; both forms are valid.

General shape:

```xml
<object
  id="some-object"
  classes="class-a class-b"
  acceptedChildren=":Proteus-any"
  acceptedParents=":Proteus-document section"
  selectedCategory="detail"
>
  <properties>
    ...
  </properties>
  <children numbered="true">
    <child id="child-1"/>
    <child id="child-2"/>
  </children>
</object>
```

Important consequence:

- Proteus stores hierarchy by reference, not by nesting full child XML inside the parent.
- Parent files contain only child IDs; the child content lives in separate files.

## Example Object Types

The default `basic` profile ships one archetype set per language under `profiles/basic/archetypes/{language}` (see `profiles/basic/archetypes/languages.xml`, same convention as the profile's `i18n` directory). For example, the English set defines its object archetypes in `profiles/basic/archetypes/en_us/objects/00_general/objects.xml` and the concrete XML templates in the sibling `objects/` directory.

The examples below are the **archetype files** of the English `basic` profile (abridged where noted), not files saved by Proteus in a project; see the note on normalization above.

### Section

`section` is a structural object. It can contain any child object and can itself appear under a document or another section.

```xml
<object
  id="section"
  classes="section"
  acceptedChildren=":Proteus-any"
  acceptedParents=":Proteus-document section"
>
  <properties>
    <stringProperty name=":Proteus-name"><![CDATA[Section]]></stringProperty>
    <markdownProperty name="comments"><![CDATA[]]></markdownProperty>
  </properties>
</object>
```

What this shows:

- A simple object may have only a few properties.
- `acceptedChildren` and `acceptedParents` define structural constraints.

### Paragraph

`paragraph` is a leaf object with rich text and traceability properties.

```xml
<object
  id="paragraph"
  classes="traceable-object paragraph"
  acceptedChildren=":Proteus-none"
  acceptedParents=":Proteus-document section"
  selectedCategory="detail"
>
  <properties>
    <stringProperty name=":Proteus-name"><![CDATA[Paragraph]]></stringProperty>
    <dateProperty name=":Proteus-date">2024-09-01</dateProperty>
    <stringProperty name="version"><![CDATA[1.0]]></stringProperty>
    <traceProperty name="authors" category="general" acceptedTargets="stakeholder" traceType=":Proteus-author"/>
    <traceProperty name="sources" category="general" acceptedTargets="stakeholder" traceType=":Proteus-information-source"/>
    <markdownProperty name="text" category="detail"><![CDATA[]]></markdownProperty>
    <traceProperty name="dependencies" category="dependencies" acceptedTargets="traceable-object" traceType=":Proteus-dependency"/>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
</object>
```

What this shows:

- A leaf node uses `acceptedChildren=":Proteus-none"`.
- `traceProperty` stores relationships to other objects by ID.
- `selectedCategory="detail"` hints which property group should be emphasized in the UI.

### Stakeholder

`stakeholder` is a good example of mixed scalar and enumerated properties.

```xml
<object
  id="stakeholder"
  classes="traceable-object stakeholder"
  acceptedChildren=":Proteus-none"
>
  <properties>
    <stringProperty name=":Proteus-name"><![CDATA[Family name, First name]]></stringProperty>
    <dateProperty name=":Proteus-date">2024-09-01</dateProperty>
    <stringProperty name="version"><![CDATA[1.0]]></stringProperty>
    <traceProperty name="authors" category="general" acceptedTargets="stakeholder" traceType=":Proteus-author"/>
    <traceProperty name="sources" category="general" acceptedTargets="stakeholder" traceType=":Proteus-information-source"/>
    <stringProperty name="role" category="detail"><![CDATA[]]></stringProperty>
    <enumProperty name="category" category="detail" choices="tbd customer developer user">tbd</enumProperty>
    <stringProperty name="phone-number" category="detail"><![CDATA[]]></stringProperty>
    <stringProperty name="email" category="detail"><![CDATA[]]></stringProperty>
    <traceProperty name="works-for" category="detail" acceptedTargets="organization" traceType=":Proteus-works-for"/>
    <fileProperty name="photo" category="detail" tooltip="file-info"><![CDATA[stakeholder_photo.png]]></fileProperty>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
  <children />
</object>
```

What this shows:

- `enumProperty` uses a whitespace-separated `choices` attribute and stores the selected value as element text.
- `traceable-object` is a general class shared by every object that can be the target of dependency traces; `stakeholder`, the last class, is the main class.
- Empty `<children />` is valid for leaf objects.

### Local Figure

`local-figure` shows how assets are referenced from object properties.

```xml
<object
  id="local-figure"
  classes="traceable-object figure"
  acceptedChildren=":Proteus-none"
>
  <properties>
    <stringProperty name=":Proteus-name"><![CDATA[US Logo (local)]]></stringProperty>
    <dateProperty name=":Proteus-date">2024-09-01</dateProperty>
    <stringProperty name="version"><![CDATA[1.0]]></stringProperty>
    <traceProperty name="authors" category="general" acceptedTargets="stakeholder" traceType=":Proteus-author"/>
    <traceProperty name="sources" category="general" acceptedTargets="stakeholder" traceType=":Proteus-information-source"/>
    <fileProperty name="file" category="detail" tooltip="file-info"><![CDATA[us-logo.jpg]]></fileProperty>
    <urlProperty name="url" category="detail"><![CDATA[]]></urlProperty>
    <integerProperty name="width" category="detail" tooltip="width-info">20</integerProperty>
    <markdownProperty name="description" category="detail"><![CDATA[University of Seville logo (local)]]></markdownProperty>
    <traceProperty name="dependencies" category="dependencies" acceptedTargets="traceable-object" traceType=":Proteus-dependency"/>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
</object>
```

What this shows:

- `fileProperty` stores a file name, not the binary file itself.
- The referenced asset is expected to exist in the project's `assets/` directory. In a profile, the default files of object archetypes live in the `assets/` directory of their category folder (e.g. `archetypes/en_us/objects/00_general/assets/us-logo.jpg`) and are copied into the project when the object is created.
- `urlProperty` can coexist with `fileProperty`; in the default profile the remote figure archetype uses the URL field instead of the local file field.

## Property Storage Rules

Properties are stored under a `<properties>` element. Each property is represented by an XML element whose tag name encodes the property type.

Examples used by the default profile include:

- `stringProperty`
- `markdownProperty`
- `dateProperty`
- `integerProperty`
- `enumProperty`
- `fileProperty`
- `urlProperty`
- `traceProperty`

The property factory in the code also supports these additional types:

- `booleanProperty`
- `timeProperty`
- `floatProperty`
- `classListProperty`
- `codeProperty`
- `traceTypeListProperty`
- `unitProperty`

Tag names are case-sensitive and must be written exactly as above (they are defined in
`proteus/model/properties/__init__.py`). **A property whose tag is not one of these is
ignored when the object is loaded**, with only a warning in the log: a misspelled tag
(e.g. `classlistProperty`) makes the property silently disappear.

Common property attributes and their default values:

| Attribute | Default | Meaning |
| --- | --- | --- |
| `name` | — | property name; also the i18n key `archetype.prop_name.<name>` |
| `category` | `general` | tab of the edit form (`archetype.prop_category.<category>`) |
| `required` | `false` | the form does not accept an empty value |
| `inmutable` | `false` | the input is locked in the form until a checkbox next to it is ticked (note the spelling) |
| `tooltip` | empty | i18n key of the tooltip: `archetype.tooltip.<tooltip>` |

Some property types add extra attributes:

- `enumProperty`: `choices`, optionally `valueTooltips="true"` to show a tooltip per choice (i18n key `archetype.enum_choices.tooltip.<property>.<choice>`).
- `traceProperty`: `acceptedTargets` (default `:Proteus-any`), `excludedTargets` (default none), `traceType` (default `:Proteus-dependency`) and `maxTargetsNumber` (default `-1`, no limit).
- `unitProperty`: uses nested `<value>` and `<unit>` elements instead of plain text, and lists the allowed units in the `units` attribute.
- `codeProperty`: uses nested `<prefix>`, `<number>`, and `<suffix>` elements.

### Reserved `:Proteus-` Property Names

Some property names are not just user-defined labels. Proteus also defines a small set of reserved property names that begin with `:Proteus-`. These names have framework-level meaning and appear repeatedly in project, document, and object XML.

Common examples are:

- `:Proteus-name`: the display name of the project or object
- `:Proteus-date`: the main date associated with the element
- `:Proteus-code`: a structured code value stored as prefix, number, and suffix
- `:Proteus-acronym`: a short acronym, commonly used in document-like objects

Typical usage looks like this:

```xml
<stringProperty name=":Proteus-name" category="general"><![CDATA[Paragraph]]></stringProperty>
<dateProperty name=":Proteus-date" category="general">2026-05-01</dateProperty>
<codeProperty name=":Proteus-code" category="general">
  <prefix>REQ-</prefix>
  <number>001</number>
  <suffix></suffix>
</codeProperty>
<stringProperty name=":Proteus-acronym" category="general"><![CDATA[DOC]]></stringProperty>
```

These names are still stored like normal properties in XML, but they are special by convention and by direct use in the codebase. When manually authoring content, it is best to keep these names for their intended semantics instead of reusing them for unrelated meanings.

### Reserved Trace Types

Trace types are free strings, but the code and the default templates rely on these ones
(`proteus/model/__init__.py`):

| Trace type | Usual meaning |
| --- | --- |
| `:Proteus-dependency` | generic dependency (default trace type) |
| `:Proteus-author` | author of an object (targets stakeholders) |
| `:Proteus-information-source` | information source (targets stakeholders) |
| `:Proteus-works-for` | a stakeholder works for an organization |
| `:Proteus-affected` | object affected by another one |
| `:Proteus-link` | target of a symbolic link |

## Examples of Every Property Type

The following example block shows the XML shape of every property type supported by the property factory.

```xml
<properties>
  <booleanProperty name="approved" category="general">true</booleanProperty>

  <stringProperty name="title" category="general"><![CDATA[System Specification]]></stringProperty>

  <dateProperty name=":Proteus-date" category="general">2026-05-01</dateProperty>

  <timeProperty name="review-time" category="general">14:30:00</timeProperty>

  <markdownProperty name="description" category="detail"><![CDATA[
This text may contain **Markdown** and multiple lines.
]]></markdownProperty>

  <integerProperty name="priority" category="detail">3</integerProperty>

  <floatProperty name="completion" category="detail">97.5</floatProperty>

  <enumProperty name="status" category="detail" choices="draft review approved">review</enumProperty>

  <fileProperty name="attachment" category="detail"><![CDATA[diagram.png]]></fileProperty>

  <urlProperty name="reference-url" category="detail"><![CDATA[https://example.org/spec]]></urlProperty>

  <classListProperty name="tags" category="detail">
    <class>requirement</class>
    <class>verified</class>
  </classListProperty>

  <codeProperty name=":Proteus-code" category="general">
    <prefix>REQ-</prefix>
    <number>001</number>
    <suffix>-A</suffix>
  </codeProperty>

  <traceProperty
    name="depends-on"
    category="dependencies"
    acceptedTargets="traceable-object"
    excludedTargets="stakeholder"
    traceType=":Proteus-dependency"
    maxTargetsNumber="3"
  >
    <trace target="a1b2c3d4e5f6" traceType=":Proteus-dependency"/>
    <trace target="z9y8x7w6v5u4" traceType=":Proteus-dependency"/>
  </traceProperty>

  <traceTypeListProperty name="allowed-traces" category="detail">
    <type>:Proteus-dependency</type>
    <type>:Proteus-author</type>
  </traceTypeListProperty>

  <unitProperty name="mass" category="detail" units="g kg lb">
    <value>2.5</value>
    <unit>kg</unit>
  </unitProperty>
</properties>
```

Notes about these formats:

- `booleanProperty` stores `true` or `false` as lowercase text.
- `stringProperty`, `markdownProperty`, `fileProperty`, and `urlProperty` store text content, wrapped in CDATA by Proteus. An empty value must be written as `<![CDATA[]]>`: a self-closing element such as `<markdownProperty name="x"/>` is loaded as the text `None`.
- `dateProperty` uses ISO date format: `YYYY-MM-DD`.
- `timeProperty` uses `HH:MM:SS`.
- `enumProperty` stores the selected value as element text and the available choices in the `choices` attribute.
- `classListProperty` stores one `<class>` child per value.
- `codeProperty` stores its value in three nested elements: `<prefix>`, `<number>`, and `<suffix>`.
- `traceProperty` stores target IDs in nested `<trace>` elements, in order. The property-level attributes define allowed targets and trace semantics. Proteus writes a `traceType` attribute on every `<trace>` too, but only reads its `target`: the trace type always comes from the property.
- `traceTypeListProperty` stores one `<type>` child per allowed trace type.
- `unitProperty` stores the numeric value and the unit in separate nested elements and lists allowed units in the `units` attribute. The value is a real number (Proteus writes `200.0`) and the unit is one of the keys listed in `units`, never its translation (labels come from `archetype.enum_units.<unit>`).

## How Hierarchy Is Represented

Proteus stores containment through ID references.

Project to documents:

```xml
<documents>
  <document id="doc-1"/>
  <document id="doc-2"/>
</documents>
```

Object to children:

```xml
<children>
  <child id="sec-1"/>
  <child id="para-1"/>
</children>
```

The actual content for `doc-1`, `sec-1`, and `para-1` is stored in separate files in `objects/`.

## How Application State Is Stored

Proteus also writes a YAML state file in the project directory. This file is not part of the domain content model; it stores UI/session state such as:

- currently selected document
- currently selected objects
- selected view
- opened views
- expanded nodes in the document tree

This means two different persistence layers coexist:

- XML for project, document, object, and property content
- YAML for editor state

## Editing Project Files by Hand

Projects can be created or changed by editing their XML files directly (e.g. with a
script). These rules keep them consistent with what Proteus itself does.

### Before editing

- **Close the project in Proteus first.** Proteus keeps the open project in memory and,
  when saving, rewrites every new or modified object and deletes the files of the objects
  removed in the application, overwriting changes made outside. Objects not modified in the
  application are not rewritten.

### Objects are copies of their archetypes

When an object is created, Proteus copies its archetype into the project: `classes`,
`acceptedChildren`, `acceptedParents` and every property **definition** (`choices`,
`units`, `tooltip`, `acceptedTargets`, ...), not just the values. Consequently:

- Changing an archetype in a profile does **not** change the objects already created from
  it. To propagate a change (e.g. a new property), edit every affected object file, adding
  the new property element at the same position as in the archetype.
- Objects do not record which archetype they come from: behaviour must depend on classes
  or properties, never on the archetype ID.

### Creating, moving and deleting objects

- New IDs must be unique in the whole project. Proteus generates 12-character short UUIDs
  (`shortuuid.random(length=12)`); manual IDs only need to match the file name.
- Creating an object means writing `objects/<id>.xml` **and** adding `<child id="<id>"/>`
  to its parent at the right position (`<document id="<id>"/>` in `proteus.xml` for a new
  document).
- Deleting an object means removing its file, its `<child>` reference in the parent, the
  files of all its descendants, and every `<trace target="<id>">` pointing to any of them.
  Incoming traces are not stored anywhere else: they are computed by scanning the project.
- **Parent/child acceptance rules and trace constraints (`acceptedTargets`,
  `excludedTargets`, `maxTargetsNumber`) are checked by the application when editing, not
  when loading**: a file that breaks them loads without errors. Respect them by hand.

### Invalid values are replaced silently

When loading, invalid values do not raise errors; they are replaced and a warning is
logged:

| Property | Invalid value | Loaded as |
| --- | --- | --- |
| `dateProperty` | not `YYYY-MM-DD` | today's date |
| `integerProperty` | not an integer | `0` |
| `enumProperty` | not in `choices` | the first choice |
| `unitProperty` | unit not in `units` | the first unit |
| text properties | self-closing element | the text `None` |
| any property | unknown tag | (property ignored) |

### What Proteus does when it clones an object or an archetype

To create objects by hand that look like the ones created by Proteus:

- Every cloned object (and descendant) gets a new ID.
- `:Proteus-date` is set to the current date.
- `:Proteus-code` gets the next number after the biggest code with the same prefix in the project (e.g. `UC-004` after `UC-003`); if there is none yet, it keeps the archetype's number (e.g. `UC-001`).
- When copying an existing object (not an archetype), its name gets a "Copy of" prefix.
- Traces between objects of the cloned subtree are redirected to the new copies; traces to
  objects outside the subtree are kept.
- Assets referenced by `fileProperty` values are copied into the project's `assets/`.

### Checking a project after editing it

A quick consistency check with the Python environment of Proteus (all files are
well-formed and every child, document and trace reference exists):

```python
import glob, xml.etree.ElementTree as ET
project = r"C:\path\to\project"
ids = {f.split("\\")[-1][:-4] for f in glob.glob(project + r"\objects\*.xml")}
for f in [project + r"\proteus.xml"] + glob.glob(project + r"\objects\*.xml"):
    for ref in ET.parse(f).getroot().iter():
        if ref.tag in ("child", "document", "trace"):
            target = ref.get("id") or ref.get("target")
            assert target in ids, f"{f}: dangling reference {target}"
print(len(ids), "objects OK")
```

For a full check, load it with the model (`Project.load(<project directory>)`) and render
it with the profile's templates.

## Practical Summary

Proteus uses a simple and robust storage strategy:

1. `proteus.xml` stores project metadata and the list of top-level documents.
2. Every document and object is a separate XML file in `objects/`.
3. Parent-child relations are stored by ID references, not by embedding child XML.
4. File-based resources referenced by properties are stored in `assets/`.
5. The archetypes of the active profile (e.g. `profiles/basic`) define the objects and the property shapes that new content starts from; each object keeps its own copy of them.
6. A YAML file (`state.yaml`) stores temporary/editor UI state independently from the content model.

For documentation purposes, the most important idea is this: in Proteus, documents are a special kind of object, and nearly the entire content structure is a graph of XML files linked together by IDs.