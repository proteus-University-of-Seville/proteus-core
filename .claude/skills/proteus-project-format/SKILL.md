---
name: proteus-project-format
description: On-disk format of PROTEUS projects (proteus.xml, objects/<id>.xml, assets/, state.yaml) and how to read, create or modify project content by editing the XML files directly instead of going through the PROTEUS MCP server. Use when inspecting or changing a PROTEUS project or a project/document archetype, when the MCP server is not running or cannot do the change (e.g. adding a property to existing objects), for bulk edits, or to validate and render a project from a script.
---

# PROTEUS project format and direct XML editing

Full reference with an example of every property type:
`C:\proteus\documentation\PROJECT_STORAGE_MANUAL.md`. This skill summarizes it and
adds the rules learned the hard way.

## MCP or direct XML?

| Use the MCP server (`mcp__proteus__*`) | Edit the XML files directly |
|---|---|
| PROTEUS is running with the project open | PROTEUS is closed |
| Creating objects from archetypes, editing property values, adding/removing traces, moving objects | Changes the MCP cannot do: adding/removing a property on existing objects, changing `classes`/`acceptedChildren`, renaming a project |
| Few, interactive changes (it validates parents, types and trace targets) | Bulk or scripted changes; creating whole test projects |

Rules:

- **Never edit the files of a project that PROTEUS has open**: it keeps the project in
  memory and overwrites the files on save. Check first:
  `Get-CimInstance Win32_Process -Filter "Name like 'python%'" | ? { $_.CommandLine -match 'proteus.exe' }`.
  Changes made through the MCP stay in memory until the user saves from the GUI.
- With the MCP, `get_document` on a big document exceeds the output limit; the result is
  saved to a file: extract what you need from it with a script.

## Layout

```text
my-project/
  proteus.xml          project file: properties + ordered list of document ids
  objects/<id>.xml     one file per document or object (file name == id)
  assets/              files referenced by fileProperty values (logos, photos, figures)
  state.yaml           GUI state only (expanded nodes, selection); safe to delete
  .gitignore           ignores state.yaml / state.yml
```

Project archetypes (in a profile, `archetypes/<lang>/projects/<name>/`) use the same layout
but the project file is named **`project.xml`**; PROTEUS renames it to `proteus.xml` when
creating a project. Document archetypes (`archetypes/<lang>/documents/<name>/`) have a
`document.xml` pointer (`<document id="the-doc-id"/>`) plus `objects/` and optional `assets/`.

## Files

`proteus.xml`:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<project id="empty">
  <properties>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[My project]]></stringProperty>
    <stringProperty name="version" category="general"><![CDATA[1.0]]></stringProperty>
    <dateProperty name=":Proteus-date" category="general">2026-09-27</dateProperty>
    <markdownProperty name="description" category="detail"><![CDATA[...]]></markdownProperty>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
  <documents>
    <document id="empty-doc"/>
  </documents>
</project>
```

`objects/<id>.xml` (documents are objects whose `classes` contain `:Proteus-document`):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<object id="8FjdDxsFfPrn" classes="traceable-object paragraph comment"
        acceptedChildren=":Proteus-none" acceptedParents=":Proteus-document section">
  <properties>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[Open issue]]></stringProperty>
    <dateProperty name=":Proteus-date" category="general">2026-09-27</dateProperty>
    <traceProperty name="authors" category="general" acceptedTargets="stakeholder" traceType=":Proteus-author">
      <trace target="ATCoftLhzaCw" traceType=":Proteus-author"/>
    </traceProperty>
    <markdownProperty name="text" category="detail"><![CDATA[**TBD.** ...]]></markdownProperty>
    <traceProperty name="dependencies" category="dependencies" acceptedTargets="traceable-object" traceType=":Proteus-dependency"/>
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>
  <children numbered="true">        <!-- optional; ordered references, never nested content -->
    <child id="b7NQKYPd3s9J"/>
  </children>
</object>
```

Property shapes most used in profiles (see the manual for all of them):

- Text: `stringProperty`, `markdownProperty`, `urlProperty`, `fileProperty` → CDATA text.
- `dateProperty` `YYYY-MM-DD`, `timeProperty` `HH:MM:SS`, `booleanProperty` `true|false`,
  `integerProperty`, `floatProperty`.
- `enumProperty choices="tbd high low"` → selected value as text.
- `codeProperty` → `<prefix>`, `<number>`, `<suffix>` children (e.g. `UC-`, `001`, ``).
- `unitProperty units="year month day"` → `<value>200.0</value><unit>day</unit>`; the value
  is a float, the unit one of the `units` keys (untranslated).
- `traceProperty acceptedTargets="..." [excludedTargets] [maxTargetsNumber="1"] traceType="..."`
  → one `<trace target="<id>" traceType="<same traceType>"/>` per target, in order.
- Other types: `classListProperty` (`<class>` children), `traceTypeListProperty`
  (`<type>` children). Tag names are case-sensitive: **an unknown or misspelled tag is
  silently ignored** (only a log warning), so the property disappears.
- Common attributes and defaults: `name`, `category` (form tab, default `general`),
  `tooltip` (i18n key `archetype.tooltip.<tooltip>`), `required` and `inmutable` (sic)
  (default `false`). `traceProperty` defaults: `traceType=":Proteus-dependency"`,
  `acceptedTargets=":Proteus-any"`, `maxTargetsNumber="-1"` (no limit). The `traceType`
  of each `<trace>` is written but not read: the property's one applies.
- Reserved trace types: `:Proteus-dependency`, `-author`, `-information-source`,
  `-works-for`, `-affected`, `-link` (symbolic links).

## Rules that matter when editing by hand

1. **File name == id.** Ids are unique in the whole project. PROTEUS generates
   12-character short UUIDs; generate the same way
   (`shortuuid.random(length=12)` in the venv) and check against existing file names.
2. **Hierarchy is by reference.** Adding an object = write `objects/<id>.xml` **and** add
   `<child id="<id>"/>` to its parent at the right position. Adding a document = also add
   `<document id=.../>` to `proteus.xml`. Deleting = remove the file, the `<child>`
   reference, and every `<trace target="<id>">` pointing to it (backlinks are not stored,
   they are computed: search all files).
3. **Objects carry a full copy of their archetype's metadata** (`classes`,
   `acceptedChildren`, `acceptedParents`, every property definition including `choices`,
   `units`, `tooltip`, `acceptedTargets`). Changing an archetype in a profile does **not**
   change existing objects: to propagate it, edit every affected object file (e.g. insert
   the new `traceProperty` after the same sibling property as in the archetype).
4. **Acceptance rules are checked by the GUI and the MCP, not when loading.** A child is
   valid only if the parent's `acceptedChildren` contains `:Proteus-any` or one of the
   child's classes **and** the child's `acceptedParents` (default `:Proteus-any`) contains
   one of the parent's classes. Respect them in manual edits.
5. **Trace targets must exist** in the project, and their classes must match
   `acceptedTargets` (and not `excludedTargets`); `maxTargetsNumber` limits the count.
6. **Assets**: a `fileProperty` stores only a file name; the file must exist in `assets/`.
7. **Empty text is `<![CDATA[]]>`**, never a self-closing element: `<markdownProperty
   name="x"/>` loads as the text `None`.
8. **Invalid values are replaced silently on load** (warning in the log only): a bad date
   becomes today, a bad integer `0`, an enum value not in `choices` the first choice, a
   unit not in `units` the first unit. Write valid values.
9. **Saving**: Proteus rewrites only new or modified objects and deletes the files of the
   objects removed in the GUI; files it did not touch keep their hand-written format.
   Saved files are normalized (`category` on every property, `acceptedParents`,
   `<children/>`, `<?xml version='1.0' encoding='UTF-8'?>`).
10. **Cloning** (what to imitate when creating objects by hand): new IDs, `:Proteus-date`
    = today, `:Proteus-code` = next number for its prefix in the project (or the
    archetype's if none), "Copy of" prefix only when copying an existing object, traces
    inside the cloned subtree redirected to the copies, referenced assets copied.
11. **Encoding and line endings**: UTF-8, CDATA for free text. When scripting edits, read
   bytes, detect `\r\n` vs `\n`, keep the original line endings and use `\r?\n` in
   regexes. Prefer inserting text next to an existing sibling over re-serializing the
   whole file with lxml (keeps diffs minimal).
12. Reserved names: `:Proteus-name`, `:Proteus-code`, `:Proteus-date`, `:Proteus-acronym`
   keep their framework meaning; `:Proteus-code` numbers are assigned on cloning.

## Validate after editing

Use the PROTEUS venv: `C:\proteus\.venv\Scripts\python.exe`. Minimal checks:

```python
import glob, xml.etree.ElementTree as ET
p = r"C:\proteus-samples\my-project"
ids = {f.split("\\")[-1][:-4] for f in glob.glob(p + r"\objects\*.xml")}
for f in [p + r"\proteus.xml"] + glob.glob(p + r"\objects\*.xml"):
    root = ET.parse(f).getroot()                      # well-formed
    for ref in root.iter():
        if ref.tag in ("child", "document", "trace"):
            target = ref.get("id") or ref.get("target")
            assert target in ids, f"{f}: dangling reference {target}"
print(len(ids), "objects OK")
```

Full load with the PROTEUS model: `Project.load(<project dir>)` (pass the directory, not
the file), then walk `project.get_descendants()` / `object.children`.

## Render a project from a script (no GUI)

Same start-up order as `proteus/app.py`. `current_document` must be set, or the
default template renders nothing:

```python
import sys; sys.path.insert(0, r"C:\proteus")
from pathlib import Path
from proteus.application.configuration.config import Config
from proteus.application.configuration.profile_settings import ProfileSettings
from proteus.application.resources.translator import Translator
from proteus.application.resources.plugins import Plugins
from proteus.application.state.manager import StateManager
from proteus.model.project import Project
from proteus.services.project_service import ProjectService
from proteus.services.render_service import RenderService

lang, profile = "es_ES", Path(r"C:\proteus-profiles\madeja")
config = Config(); config.app_settings.language = lang
config.profile_settings = ProfileSettings.load(profile, lang)
t = Translator(); t.set_language(lang)
t.set_proteus_i18n_directory(config.app_settings.i18n_directory)
t.load_translations(config.app_settings.i18n_directory)
t.load_translations(config.profile_settings.i18n_directory)
Plugins().load_plugins(config.app_settings.plugins_directory)
project = Project.load(r"C:\proteus-samples\my-project")
StateManager().set_current_document(project.get_descendants()[0].id)
service = ProjectService(); service.project = project
render = RenderService(); render.add_functions_to_namespace(Plugins().get_xslt_functions())
html = render.render(service.generate_project_xml(), "default")
```

Check the HTML for `!some.key!` (missing translations) and for an `<errors>` root (XSLT
errors, also logged as CRITICAL). To look at it, replace `templates:///` with
`file:///<profile>/xslt/` and `assets:///` with the project's `assets/` URL; screenshots
need QtWebEngine with a real window (`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`,
`QT_OPENGL=software`), the offscreen platform renders blank.

Objects can also be created programmatically from archetypes:
`ArchetypeRepository.load_object_archetypes(<profile>/archetypes/<lang>)` →
`archetype.clone_object(parent, project)`, set values with
`obj.set_property(obj.get_property(name).clone(value))`, then `project.save_project()`.
