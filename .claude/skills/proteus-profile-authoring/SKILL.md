---
name: proteus-profile-authoring
description: How a PROTEUS profile is organized (profile.ini, per-language archetypes, i18n YAML, icons, XSLT templates, CSS) and step-by-step checklists to create a new profile from an existing one (usually the basic profile shipped in C:\proteus\profiles\basic) and to add or change object archetypes, listing every file to create and every file to modify. Use when creating, extending or reviewing a profile such as madeja (C:\proteus-profiles\madeja).
---

# PROTEUS profile authoring

Related docs in `C:\proteus\documentation`: `archetype_tasks.md` (step-by-step guide to add
an object archetype, the human-oriented version of the checklist below),
`i18n_design.md`, `PROJECT_STORAGE_MANUAL.md`. For the XML of objects and properties see
the `proteus-project-format` skill.

## Where profiles live and how one is selected

- Profiles shipped with the app: `C:\proteus\profiles\<name>` (`basic`).
- External profiles have their own repository, e.g. `C:\proteus-profiles\madeja`
  (GitHub `proteus-University-of-Seville/profile-madeja`).
- The app configuration `C:\proteus\proteus.ini` selects the profile:
  `selected_profile = basic`, `using_default_profile = False`,
  `custom_profile_path = C:/proteus-profiles/madeja`. PROTEUS loads the profile (archetypes,
  translations, icons, templates) **at start-up**: restart it after changing a profile.
- A profile is a **copy** of another profile plus changes; there is no inheritance between
  profiles. Changes to `basic` that should also apply to `madeja` must be made in both.

## Profile layout

```text
<profile>/
  profile.ini                 [directories] archetypes/xslt/icons/i18n/plugins dirs,
                              [preferences] default_view, [information] name/description/image
  archetypes/
    languages.xml             <languages default="en_us"><language key="en_US" path="en_us"/>...
    <lang>/                   one complete archetype set per language (en_us, es_es)
      projects/<name>/        project.xml, objects/, assets/, .gitignore
      documents/<name>/       document.xml (<document id="..."/>), objects/<id>.xml, assets/
      objects/
        NN_<category>/        NN orders the toolbar tabs; <category> is the tab key
          objects.xml         ordered list of archetype ids of this tab: ONLY these are loaded
          objects/<id>.xml    one file per object archetype
          assets/             files referenced by fileProperty defaults of this category
  i18n/
    languages.xml             same format as archetypes/languages.xml
    <lang>/*.yaml             all files of a language are merged in one dictionary
  icons/
    <main-class>.png          48x48 toolbar/tree icon, found by convention
    icons.xml                 optional overrides (app, document, menu icons)
  xslt/<template>/            e.g. default/
    template.xml              entry point (default.xsl) and plugin dependencies
    default.xsl               includes core/*.xsl and one module per archetype
    core/                     utilities, generate_table, properties, cover, document
    archetypes/<category>/<archetype>.xsl
    resources/css/            default.css @imports one CSS per archetype
    resources/images, javascript
  xslt/latex/                 basic only: LaTeX template (template.xml output="latex"), not a
                              view; same structure, latex.xsl entry, resources/proteus.sty
  plugins/                    optional (plugins_directory in profile.ini)
```

## Create a new profile from an existing one

1. Copy the whole source profile directory (e.g. `profiles/basic`) to the new location
   (e.g. `C:\proteus-profiles\<new>`), ideally as a new git repository.
2. `profile.ini`: change `[information]` `name`, `description` and `image` (put the image
   in `icons/`). Keep `[directories]` unless you rename folders.
3. Languages: keep `archetypes/languages.xml` and `i18n/languages.xml` consistent; every
   language listed needs a full `archetypes/<lang>/` set and an `i18n/<lang>/` folder.
4. Project archetypes (`archetypes/<lang>/projects/`): rename folders, edit `project.xml`
   (`id`, name, description). Give each language its own project `id`.
5. Document archetypes: one folder per document type; `document.xml` points to the
   document object in `objects/`, which lists its children (sections, paragraphs...) as
   `<child id>` of files in the same `objects/` folder.
6. Object archetypes: add, remove or reorganize categories (`NN_<category>` folders) and
   archetypes following the checklist below; remove the ids of deleted archetypes from
   `objects.xml` and their XSLT includes, CSS imports and icons.
7. Point `proteus.ini` to the new profile, start PROTEUS and create a project from each
   project archetype; render it with the `default` view.

## Add a new object archetype: checklist

Do every step for **every language** (`en_us`, `es_es`): the archetype sets must keep the
same ids, classes and properties; only texts change.

### Files to create

| File | Notes |
|---|---|
| `archetypes/<lang>/objects/NN_<category>/objects/<id>.xml` | the archetype (see rules below) |
| `icons/<main-class>.png` | 48x48, flat style of the profile; `<main-class>` = last class in `classes` |
| `xslt/default/archetypes/<category>/<id_with_underscores>.xsl` | only if the generic rendering (`any_archetype.xsl`, a property table) is not enough |
| `xslt/default/resources/css/<id_with_underscores>.css` | optional accent colour: `.proteus_table.<main-class> { --accent: #1d4ed8; }` |
| `archetypes/<lang>/objects/NN_<category>/assets/<file>` | only if a `fileProperty` default points to a file |
| `archetypes/<lang>/objects/NN_<category>/` + `objects.xml` + `objects/` | only for a new category (tab) |

### Files to modify

| File | Change |
|---|---|
| `archetypes/<lang>/objects/NN_<category>/objects.xml` | add `<object id="<id>" />` where it must appear in the tab; unlisted archetypes are **not loaded at all** (child-only archetypes must be listed too) |
| `i18n/<lang>/archetypes.yaml` (basic: `basic_archetypes.yaml`) | `archetype.class.<class>` for **every** class tag used (also abstract ones: they appear in class lists, e.g. traceability matrix rows); `archetype.prop_name.<property>` for new property names; `archetype.enum_choices.<choice>`; `archetype.enum_choices.tooltip.<property>.<choice>` if `valueTooltips="true"`; `archetype.enum_units.<unit>` for unitProperty units; `archetype.tooltip.<tooltip>`; `archetype.prop_category.<category>` for a new form tab; `archetype.category.<category>` for a new toolbar tab |
| `i18n/<lang>/xslt_labels.yaml` | `xslt.<name>` literal texts used by the new XSLT module (move them out of `xslt_pending_labels.yaml` if they were there) |
| `xslt/default/default.xsl` | `<xsl:include href="archetypes/<category>/<id>.xsl" />` in its category block |
| `xslt/default/resources/css/default.css` | `@import url('<id>.css');` if a CSS file was created |
| archetypes that must accept/trace the new one | their `acceptedChildren`, `acceptedParents` or a trace's `acceptedTargets` |

### Archetype XML rules

```xml
<?xml version="1.0" encoding="UTF-8"?>
<object
    id="use-case"                                   (= file name; unique in the profile)
    classes="software-requirement use-case"         (general → specific; LAST = main class)
    acceptedChildren="use-case-step conditional-branch"   (or :Proteus-any / :Proteus-none)
    acceptedParents="..."                           (optional, default :Proteus-any)
>
  <properties>
    <codeProperty name=":Proteus-code" category="general" inmutable="true">
      <prefix><![CDATA[UC-]]></prefix><number>001</number><suffix><![CDATA[]]></suffix>
    </codeProperty>
    <stringProperty name=":Proteus-name" category="general" tooltip="use-case-name">Concrete use case</stringProperty>
    ...
  </properties>
  <children numbered="true">
  </children>
</object>
```

- **Main class (last in `classes`)** decides: the toolbar button of first-level archetypes
  or the context menu entry of second-level ones (archetypes with the same main class
  become variants of one button/submenu, e.g. `use-case` and `abstract-use-case`), the
  icon file name, the class label in the HTML pill and the CSS class of the table. Give an
  archetype its own main class if it must have its own entry and icon.
- **Abstract classes** are just class tags without archetype (e.g. `use-case-step`,
  `use-case-action`). Use them in `acceptedChildren`, `acceptedParents` and
  `acceptedTargets` to model generalizations, and in XSLT to match families of archetypes.
- A child is accepted only if the parent's `acceptedChildren` contains one of the child's
  classes **and** the child's `acceptedParents` contains one of the parent's classes. Use
  both sides to forbid nesting (e.g. non-recursive conditional branches, no steps inside
  exceptions).
- `category` of each property = tab of the edit form; order of properties = order in the
  form and in the generic HTML table.
- Pre-populated children: inside `<children>`, `<object id="<sibling-archetype-id>"/>`
  clones that sibling archetype as a child (e.g. information requirement → specific data).
- Linguistic patterns go in default values, with placeholders in italics, e.g.
  `when _[triggering event]_` (as in information requirements), plus a tooltip that says
  what to replace. Prefer one archetype per pattern (concrete vs abstract use case).
- Do not rely on the archetype id at run time: objects do not remember which archetype
  they come from. Use classes or properties (e.g. `is-abstract`) for behaviour.
- **First-level** archetypes (`acceptedParents` contains `:Proteus-any` or
  `:Proteus-document`) get a toolbar button, enabled only when the selected object accepts
  them. **Second-level** archetypes (neither of those, e.g. use case steps, specific data)
  have **no toolbar button**: they appear in the context menu of objects that accept them
  **and** list one of their classes explicitly in `acceptedChildren`
  (`ArchetypeService.get_first_level_object_archetypes` /
  `get_accepted_object_archetypes`). Both kinds must be listed in `objects.xml`.
- Developer features → context menu "store as archetype" writes the object into the
  category folder of the **current language only**, appends it to `objects.xml` and copies
  its assets, but keeps the object's random 12-character id and current values: rename
  file and id (also in `objects.xml`), clean values, and create the other languages.

### i18n rules

- Keys are lowercase with `_` instead of spaces (lookups normalize the key, loading does
  not); quote values. `\n` in a class label breaks the toolbar button text; everywhere
  else (forms, HTML) it is replaced by a space.
- File names do not matter: every `*.yaml` and `*.yml` of `i18n/<lang>/` (subfolders too)
  is loaded. An empty YAML file stops the loading of the remaining files (error in the log).
- A key must be defined **once** across all YAML files of a language (later files silently
  override earlier ones; inside one file YAML keeps the last). Check with a script that
  counts keys over `i18n/<lang>/*.yaml`.
- Profile translations are loaded after the application ones (`resources/i18n/<lang>/`)
  and override keys with the same name; reuse application keys such as
  `archetype.class.:proteus-document` instead of redefining them.
- Template (view) names: `xslt_templates.<template>` and
  `xslt_templates.description.<template>`.
- A missing key renders as `!key!` in the HTML; in the GUI it shows the raw name or the
  key itself, depending on the widget, and the translator logs a warning.
- `proteus-utils:i18n(key, arg...)`: extra arguments are `{0}` format arguments, **not** a
  fallback text.

### XSLT rules

- Match by class, with priority 1 (subclasses use higher priorities and may call the
  superclass template by name):
  `match="object[contains(concat(' ', normalize-space(@classes), ' '),' use-case ')]"`.
- Reuse `generate_table` (core/generate_table.xsl): parameters `span`,
  `excluded_properties` (`',a,b,'`), `included_properties`, `extra_rows_before` (custom
  rows built in a variable), `extra_rows`, `show_children`, `postfix` (text after the name),
  `image`. Rows: `generate_property_row` (with `span` for 2-column cards).
  Markdown: `generate_markdown` (single paragraphs are not wrapped in `<p>`, so they can be
  inlined in sentences). Property-type rendering lives in `core/properties.xsl`
  (traceProperty, enumProperty, unitProperty, fileProperty...); a more specific match
  pattern in an archetype module overrides it for one property.
- Hide empty values like the rest of the profile: the generic rows already skip empty
  text and enum `tbd`; other "empty" values need custom code (e.g. madeja's use case
  excludes a frequency of `0` via `excluded_properties`).
- CSS: generic cell rules use `table.proteus_table > tbody > tr > td`; rules for a new
  row class need at least that specificity to win.
- LaTeX template (`xslt/latex`, used by the "LaTeX" and "PDF (from LaTeX)" exports): an
  archetype with a custom HTML module usually needs a LaTeX module too (included in
  `latex.xsl`) and its accent in `resources/proteus.sty` (`\ProteusSetAccent`). Escape all
  texts (`tex`/`label` named templates), never write raw `~ " < >`. Rules in
  `documentation/latex_export.md`.

## Verify

Use `C:\proteus\.venv\Scripts\python.exe` with `sys.path.insert(0, r"C:\proteus")`:

```python
import pathlib, logging; logging.disable(logging.CRITICAL)
from proteus.application.configuration.config import Config
from proteus.application.configuration.profile_settings import ProfileSettings
Config().profile_settings = ProfileSettings.load(pathlib.Path(r"<profile>"), "en_US")
from proteus.services.archetype_service import ArchetypeService
s = ArchetypeService()
for tab, groups in s.get_first_level_object_archetypes().items():   # toolbar tabs/buttons
    print(tab, {cls: [a.id for a in lst] for cls, lst in groups.items()})
uc = s.archetype_index["use-case"]
print({cls: [a.id for a in lst]                                      # context menu of a parent
       for cls, lst in s.get_accepted_object_archetypes(uc).items()})
print(uc.accept_descendant(s.archetype_index["system-step"]))       # acceptance matrix
```

Repeat with the other languages (`"es_ES"`). Then: YAML parses and has no duplicated keys;
render a test project built from the new archetypes in both languages (see the render
snippet in `proteus-project-format`) and check there is no `!key!`; finally look at it in
the GUI (forms, tooltips, toolbar, context menus, tree).

## Line endings and commits

The repositories store LF and use `core.autocrlf=true`; working copies may be CRLF. When
scripting edits, keep each file's line endings (`\r?\n` in regexes). Profile repositories
are separate from proteus-core: commit and push each one on its own branch.
