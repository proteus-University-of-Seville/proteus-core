Creating a profile
==================

A **profile** configures Proteus for a domain: it provides the project, document and object
archetypes, their translations and icons, and the XSLT templates (views) that render the
documents. Proteus ships the `basic` profile (`profiles/basic`); other profiles live in
their own folder or repository (e.g. madeja). The profile is selected in the settings dialog
(or in `proteus.ini`: `using_default_profile = False`,
`custom_profile_path = <profile folder>`) and is loaded **at start-up**: restart Proteus after
changing it.

There is no inheritance between profiles. **The safest way to create a profile is to copy
`profiles/basic` and change it**, rather than writing the files from scratch: most of the
files below have a strict format, and a profile with any of the errors marked as
*rejected* below is refused by the settings dialog ("not a valid profile").

Related documents: `archetype_tasks.md` (adding an object archetype),
`PROJECT_STORAGE_MANUAL.md` (XML of projects, documents, objects and properties),
`i18n_design.md` (translations), `latex_export.md` (LaTeX template).


1. Layout
---------

```text
<profile>/
  profile.ini
  archetypes/
    languages.xml
    <lang>/                       one complete archetype set per language (en_us, es_es...)
      projects/<folder>/          project archetypes (at least one)
        project.xml
        objects/<id>.xml          the documents of the project and all their descendants
        assets/
      documents/<folder>/         optional: standalone document archetypes
        document.xml
        objects/<id>.xml
        assets/
      objects/
        NN_<category>/            one toolbar tab per folder (see archetype_tasks.md)
          objects.xml
          objects/<id>.xml
          assets/
  i18n/
    languages.xml
    <lang>/*.yaml
  icons/
    <main-class>.png
    icons.xml                     optional
  xslt/
    default/                      one folder per template; at least one HTML view
      template.xml
      default.xsl
      core/ archetypes/ resources/
    latex/                        optional LaTeX template (export to LaTeX and PDF)
  plugins/                        optional
```


2. `profile.ini`
----------------

The key names are fixed; any other name is ignored. Paths are relative to the profile
folder.

```ini
[directories]
archetypes_directory = archetypes
xslt_directory = xslt
icons_directory = icons
i18n_directory = i18n
plugins_directory =

[preferences]
default_view = default

[information]
name = My profile
description = What the profile is for
image = icons/my_logo.png
```

| Key | Rule |
| --- | --- |
| `archetypes_directory`, `xslt_directory` | mandatory, the folder must exist (*rejected* otherwise; e.g. `archetypes = archetypes` is not read) |
| `icons_directory`, `i18n_directory`, `plugins_directory` | optional; a missing folder is ignored with a warning |
| `default_view` | name of an HTML template of `xslt/` |
| `name` | mandatory |
| `description` | optional |
| `image` | path relative to the **profile folder** (not to `icons/`); a missing file falls back to a default image |


3. `languages.xml`
------------------

`archetypes/languages.xml` and `i18n/languages.xml` have the same format and should list
the same languages. Every listed language needs a complete `archetypes/<path>/` set and an
`i18n/<path>/` folder.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<languages default="en_us">
    <language key="en_US" path="en_us" />
    <language key="es_ES" path="es_es" />
</languages>
```


4. Project archetypes
---------------------

A project archetype is a project folder whose index file is called `project.xml` instead of
`proteus.xml`; its format is **exactly** that of `proteus.xml`
(`PROJECT_STORAGE_MANUAL.md`):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<project id="my-project">
  <properties>
    <stringProperty name=":Proteus-name" category="general"><![CDATA[My project]]></stringProperty>
    <stringProperty name="version" category="general"><![CDATA[1.0]]></stringProperty>
    <dateProperty name=":Proteus-date" category="general">2026-10-19</dateProperty>
    <markdownProperty name="description" category="detail"><![CDATA[What it contains.]]></markdownProperty>
  </properties>
  <documents>
    <document id="my-doc"/>
  </documents>
</project>
```

* `<properties>` is mandatory (*rejected* without it). The name and the description are
  **properties** (`:Proteus-name`, `description`), not attributes of `<project>`.
* Each `<document id>` must be a file `objects/<id>.xml` in the same project folder, and its
  children files too.
* Every document of a project archetype is **also offered as a document archetype**. Do not
  repeat it in `documents/`; exclude it with `documentArchetype="false"` if it must not be
  offered on its own.


5. Document archetypes (optional)
---------------------------------

A folder of `documents/` needs a `document.xml` and an `objects/` folder (*rejected* without
`objects/`). `document.xml` only points to the document object, which must be
`objects/<id>.xml` of the **same folder**, together with all its descendants:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<document id="my-doc"/>
```

The `documents/` folder can be omitted (basic has none).


6. Document objects
-------------------

A document is an object whose `classes` contains `:Proteus-document`:

```xml
<object id="my-doc" classes=":Proteus-document" acceptedChildren=":Proteus-any">
```

* Other classes may follow (e.g. `":Proteus-document project-charter"`) to tell document
  types apart in custom XSLT. Templates must test the class as a token,
  `object[contains(concat(' ', normalize-space(@classes), ' '), ' :Proteus-document ')]`,
  never `@classes=':Proteus-document'`; the document template of basic and madeja has
  `priority="10"` so that no archetype module (priority 1 or 2) takes a document because
  of its other classes. Profiles whose `core/document.xsl` was copied from basic before
  October 2026 still use the exact match: copy the new `core` files.
* `acceptedChildren` restricts what can be put at the top level of the document (e.g.
  `"section"`). `acceptedParents` is not needed.
* Documents are not object archetypes: do not put them in `objects/NN_<category>/` nor list
  them in `objects.xml`. They come from project (or document) archetypes.
* The default view shows `version`, `:Proteus-date`, `prepared-by` and `prepared-for` on
  the cover (see the basic documents for their definition).


7. Object archetypes
--------------------

See `archetype_tasks.md`. The points most often got wrong:

* `:Proteus-any` and `:Proteus-none` are wildcards for `acceptedChildren`,
  `acceptedParents` and `acceptedTargets`; they are **not classes**. A section is
  `classes="section"`, not `classes=":Proteus-any section"`.
* An archetype gets a **toolbar button** only if its `acceptedParents` contains
  `:Proteus-any` or `:Proteus-document`. With `acceptedParents="section"` it is a
  second-level archetype: no button, and since sections accept `:Proteus-any` it is not in
  their context menu either, so it **cannot be created at all**. Use
  `acceptedParents=":Proteus-document section"` for content that goes in documents and
  sections.
* Every `enumProperty` needs a `choices` attribute (space-separated values, no spaces inside
  a value); without it the only choice is the default value (warning in the log).
* A `traceProperty` should declare `acceptedTargets` (default `:Proteus-any`) and, if it is
  not a plain dependency, `traceType`.
* Children pre-populated in an archetype are siblings of the same `objects/` folder, listed
  in `objects.xml` too.


8. Translations (`i18n/<lang>/*.yaml`)
--------------------------------------

See `i18n_design.md` and step 5 of `archetype_tasks.md`. In short:

* **Write every key in lowercase**: the translator lowercases the key it looks for, but not
  the keys it loads. `archetype.prop_name.documentAuthor` is never found; write
  `archetype.prop_name.documentauthor`. (Property names themselves may use any case.)
* The toolbar tab label is `archetype.category.<category>` **without** the `NN_` prefix of
  the folder (`01_initiating` → `archetype.category.initiating`).
* Define `archetype.class.<class>` for every class used, abstract ones included (e.g.
  `traceable-object`), `archetype.prop_name.<property>` for every property and
  `archetype.enum_choices.<choice>` (lowercase) for every enum choice.
* Do not redefine application keys such as `archetype.class.:proteus-document`
  (`resources/i18n/<lang>/`); profile keys override them.
* A key must be defined once across all the files of a language.
* The XSLT templates copied from basic need their labels too: copy
  `xslt_labels.yaml` and `xslt_templates.yaml` from `profiles/basic/i18n/<lang>/`, and the
  keys `archetype.prop_name.version`, `date`, `description`, `prepared-by` and
  `prepared-for` from `basic_archetypes.yaml`. A missing key shows as `!key!` in the
  rendered document.


9. XSLT templates (`xslt/<template>/`)
--------------------------------------

Each subfolder of `xslt/` is a template, described by its `template.xml`. Its format is
fixed (*rejected* if no folder has a valid HTML template):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<template name="default">
    <entryPoints default="default.xsl"/>
    <dependencies>
        <pluginDependency name="basic"/>
    </dependencies>
</template>
```

* `name` is an **attribute** of `<template>` (not a `<name>` element) and is the name used
  by `default_view` and by the i18n keys `xslt_templates.<name>` and
  `xslt_templates.description.<name>`.
* `<entryPoints default="...">` is mandatory and the file must exist.
* `<dependencies>` is mandatory, even if empty. `pluginDependency` names a plugin of the
  application (`resources/plugins`, e.g. `basic`, which provides the `proteus-utils:`
  XSLT functions used by the basic template) or of the profile.
* `output="latex"` marks a template that is not a view (the LaTeX export); HTML is the
  default.

Do not write the HTML view from scratch: a minimal stylesheet that only applies templates
produces bare text. **Copy `profiles/basic/xslt/default`** (and `xslt/latex` for the LaTeX
and PDF exports). Its generic module `archetypes/any_archetype.xsl` already renders any
archetype as a card with one row per non-empty property, so a new profile needs no XSLT at
all until it wants a custom rendering (`archetype_tasks.md`, steps 6 and 7).


10. Check the profile
---------------------

The settings dialog runs `ProfileSettings.load(<profile folder>)` and shows the first error.
To see all the problems at once, load it from a script with the Proteus Python environment
(`.venv`) and logging enabled:

```python
import sys, pathlib, logging; sys.path.insert(0, r"C:\proteus")
logging.basicConfig(level=logging.WARNING)
from proteus.application.configuration.config import Config
from proteus.application.configuration.profile_settings import ProfileSettings
Config().profile_settings = ProfileSettings.load(pathlib.Path(r"<profile>"), "es_ES")
from proteus.services.archetype_service import ArchetypeService
print(ArchetypeService().get_first_level_object_archetypes())   # toolbar tabs and buttons
```

* An `AssertionError` names the file and the rule broken.
* `ERROR ... Could not load template` means a wrong `template.xml`;
  `Could not load archetype repository` a wrong archetype folder.
* `WARNING ... Empty set of choices` means an `enumProperty` without `choices`.
* Every archetype that must be created from the toolbar must appear in the printed tabs.

Then create a project from each project archetype, add one object of each archetype,
render every document with the default view and look for `!key!` and XSLT errors
(logged as CRITICAL).
