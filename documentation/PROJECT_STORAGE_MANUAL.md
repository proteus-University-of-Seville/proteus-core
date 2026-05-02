# Proteus Project Storage Manual

This note summarizes how Proteus stores project data on disk. It is based on the runtime model in the code and on the XML archetypes shipped in `profiles/basic`.

## Overview

Proteus stores project content as XML files inside a project directory.

- The project itself is stored in `proteus.xml`.
- Documents and normal objects are stored as separate XML files in the `objects/` directory.
- Binary or linked assets used by `fileProperty` values live in `assets/`.
- A separate YAML file stores UI state such as the selected document, selected objects, expanded tree nodes, and opened views.

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
```

Notes:

- The exact YAML state filename is defined by the application state module and is separate from the project content files.
- The runtime model uses `proteus.xml` as the project file name and `objects/` and `assets/` as the conventional content directories.

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
- `classes`: one or more class tags.
- `acceptedChildren`: which child classes are allowed.
- `acceptedParents`: which parents are allowed.
- `selectedCategory`: optional UI hint for the preferred property category.
- `<properties>`: the object's properties.
- `<children>`: references to child object IDs.

Attribute rules for parent/child constraints:

- `acceptedChildren` is mandatory in `<object>` and must be present.
- `acceptedChildren` can be `:Proteus-any` (accept any child class), `:Proteus-none` (leaf object), or one or more specific class names.
- `acceptedParents` is optional.
- If `acceptedParents` is omitted, its default behavior is `:Proteus-any`.

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

The default `basic` profile defines its object archetypes in `profiles/basic/archetypes/objects/00_general/objects.xml` and the concrete XML templates in the sibling `objects/` directory.

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
  classes="general-traceable-object paragraph"
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
    <traceProperty name="dependencies" category="dependencies" acceptedTargets="general-traceable-object" traceType=":Proteus-dependency"/>
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
  classes="stakeholder"
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
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
  <children />
</object>
```

What this shows:

- `enumProperty` uses a whitespace-separated `choices` attribute and stores the selected value as element text.
- Empty `<children />` is valid for leaf objects.

### Local Figure

`local-figure` shows how assets are referenced from object properties.

```xml
<object
  id="local-figure"
  classes="general-traceable-object figure"
  acceptedChildren=":Proteus-none"
>
  <properties>
    <stringProperty name=":Proteus-name"><![CDATA[Local figure]]></stringProperty>
    <dateProperty name=":Proteus-date">2024-09-01</dateProperty>
    <stringProperty name="version"><![CDATA[1.0]]></stringProperty>
    <traceProperty name="authors" category="general" acceptedTargets="stakeholder" traceType=":Proteus-author"/>
    <traceProperty name="sources" category="general" acceptedTargets="stakeholder" traceType=":Proteus-information-source"/>
    <fileProperty name="file" category="detail" tooltip="file-info"><![CDATA[us-logo.jpg]]></fileProperty>
    <urlProperty name="url" category="detail"><![CDATA[]]></urlProperty>
    <integerProperty name="width" category="detail" tooltip="width-info">20</integerProperty>
    <markdownProperty name="description" category="detail"><![CDATA[University of Seville logo]]></markdownProperty>
    <traceProperty name="dependencies" category="dependencies" acceptedTargets="general-traceable-object" traceType=":Proteus-dependency"/>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
</object>
```

What this shows:

- `fileProperty` stores a file name, not the binary file itself.
- The referenced asset is expected to exist in the project's `assets/` directory.
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
- `classlistProperty`
- `codeProperty`
- `tracetypelistProperty`
- `unitProperty`

Common property attributes are:

- `name`
- `category`
- `required`
- `inmutable`
- `tooltip`

Some property types add extra attributes:

- `enumProperty`: `choices`, optionally `valueTooltips`
- `traceProperty`: `acceptedTargets`, `excludedTargets`, `traceType`, `maxTargetsNumber`
- `unitProperty`: uses nested `<value>` and `<unit>` elements instead of plain text
- `codeProperty`: uses nested `<prefix>`, `<number>`, and `<suffix>` elements

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

  <classlistProperty name="tags" category="detail">
    <class>requirement</class>
    <class>verified</class>
  </classlistProperty>

  <codeProperty name=":Proteus-code" category="general">
    <prefix>REQ-</prefix>
    <number>001</number>
    <suffix>-A</suffix>
  </codeProperty>

  <traceProperty
    name="depends-on"
    category="dependencies"
    acceptedTargets="general-traceable-object"
    excludedTargets="stakeholder"
    traceType=":Proteus-dependency"
    maxTargetsNumber="3"
  >
    <trace target="a1b2c3d4e5f6" traceType=":Proteus-dependency"/>
    <trace target="z9y8x7w6v5u4" traceType=":Proteus-dependency"/>
  </traceProperty>

  <tracetypelistProperty name="allowed-traces" category="detail">
    <type>:Proteus-dependency</type>
    <type>:Proteus-author</type>
  </tracetypelistProperty>

  <unitProperty name="mass" category="detail" units="g kg lb">
    <value>2.5</value>
    <unit>kg</unit>
  </unitProperty>
</properties>
```

Notes about these formats:

- `booleanProperty` stores `true` or `false` as lowercase text.
- `stringProperty`, `markdownProperty`, `fileProperty`, and `urlProperty` usually store text content, commonly wrapped in CDATA when free-form text is expected.
- `dateProperty` uses ISO date format: `YYYY-MM-DD`.
- `timeProperty` uses `HH:MM:SS`.
- `enumProperty` stores the selected value as element text and the available choices in the `choices` attribute.
- `classlistProperty` stores one `<class>` child per value.
- `codeProperty` stores its value in three nested elements: `<prefix>`, `<number>`, and `<suffix>`.
- `traceProperty` stores target IDs in nested `<trace>` elements. The property-level attributes define allowed targets and trace semantics.
- `tracetypelistProperty` stores one `<type>` child per allowed trace type.
- `unitProperty` stores the numeric value and the unit in separate nested elements and lists allowed units in the `units` attribute.

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

## Practical Summary

Proteus uses a simple and robust storage strategy:

1. `proteus.xml` stores project metadata and the list of top-level documents.
2. Every document and object is a separate XML file in `objects/`.
3. Parent-child relations are stored by ID references, not by embedding child XML.
4. File-based resources referenced by properties are stored in `assets/`.
5. The profile XML under `profiles/basic` defines the object archetypes and the property shapes that new content starts from.
6. A YAML file stores temporary/editor UI state independently from the content model.

For documentation purposes, the most important idea is this: in Proteus, documents are a special kind of object, and nearly the entire content structure is a graph of XML files linked together by IDs.