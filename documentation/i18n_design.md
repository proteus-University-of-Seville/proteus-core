i18n design in Proteus XSLT
===========================

Localized strings used by the XSLT templates are **not** part of the templates.
They are stored in the same YAML translation files used by the application GUI
and are retrieved at render time with the `proteus-utils:i18n()` extension
function.

Consequences of this design:

* XSLT templates are **language-independent**: there is one single entry point
  per template (`default.xsl`) instead of one per language.
* Adding labels for a new archetype **does not require modifying any XSLT file
  nor any existing translation file**: a new YAML file in
  `<profile>/i18n/<lang>/` is enough, since the `Translator` loads every YAML
  file found in the language directory.
* Labels are shared with the GUI, so an archetype class, property or
  enumeration choice is translated once and shown the same way in the object
  form and in the rendered document.
* Missing translations are logged by the `Translator` and rendered as `!key!`,
  instead of silently producing an empty cell, so a missing label is easy to
  spot in the rendered document regardless of where it comes from.

How it works
------------

`RenderService` registers a built-in function in the `proteus-utils` XSLT
namespace (`proteus/services/render_service.py`):

| Function | Behaviour when the key is missing |
| --- | --- |
| `proteus-utils:i18n(key, ...)` | returns `!key!` |

It calls `proteus.application.resources.translator.translate()`, which looks
the key up in the translations of the current application language, loaded from
the application `resources/i18n/<lang>/` and the profile `<profile>/i18n/<lang>/`
directories. Optional arguments are formatted into the translation
(`{0}` placeholders, with Python's `str.format()`), as in the rest of the
application.

**The extra arguments of `i18n()` are format arguments, not a fallback text**:
`proteus-utils:i18n('archetype.enum_units.day', 'day')` does not return `day` when
the key is missing (it returns `!archetype.enum_units.day!`). When arguments are
passed, literal braces in the translation must be doubled (`{{`, `}}`).

How translations are loaded and looked up (`Translator` in
`proteus/application/resources/translator.py`):

* The language directory is chosen with the `languages.xml` file of each i18n
  directory. If the current language is not listed, the `default` language of
  that file is used.
* The application translations are loaded first and the profile translations
  afterwards, into the same dictionary: **a profile key overrides an application
  key with the same name** (e.g. `archetype.class.:proteus-document`), whether on
  purpose or by accident.
* Inside a language directory, every `*.yaml` file and then every `*.yml` file is
  loaded, **including those in subdirectories**, in file system order; each file
  overrides the keys already loaded. If a file cannot be loaded (e.g. an empty
  YAML file, which is not a dictionary), an error is logged and the remaining
  files of the directory are not loaded.
* Lookups convert the key to lowercase and replace spaces with underscores.
* By default the translation of `\n` is replaced with a space: only the toolbar
  buttons keep line breaks. A class label such as `"Use\ncase"` is shown in two
  lines in the toolbar and as `Use case` everywhere else, including the rendered
  documents.

Fixed keys are written literally:

```xml
<xsl:value-of select="proteus-utils:i18n('xslt.figure')"/>
```

Keys which depend on the object being rendered are computed with `concat()`.
A profile defining a class, property, enumeration choice or trace type must
also provide its translation, otherwise `!key!` is shown, which is deliberate:
it flags a profile i18n gap instead of masking it with a raw value.

```xml
<!-- class label, e.g. archetype.class.organization -->
<xsl:value-of select="proteus-utils:i18n(concat('archetype.class.', $class))"/>

<!-- property label, e.g. archetype.prop_name.address -->
<xsl:param name="label" select="proteus-utils:i18n(concat('archetype.prop_name.', current()/@name))"/>

<!-- enumeration choice, e.g. archetype.enum_choices.developer -->
<xsl:value-of select="proteus-utils:i18n(concat('archetype.enum_choices.', current()/text()))"/>

<!-- trace type, e.g. xslt.trace_type.:Proteus-works-for -->
<xsl:value-of select="proteus-utils:i18n(concat('xslt.trace_type.', current()/text()))"/>
```

Note that keys are case-insensitive: `Translator.text()` lowercases them, so
`:Proteus-date` and `:proteus-date` are the same key. Keys are **not** lowercased
when the YAML files are loaded, so keys in the YAML files must be written in
lowercase (and with `_` instead of spaces), otherwise they are never found.

Key conventions
---------------

| Key | Content | Used by |
| --- | --- | --- |
| `archetype.class.<class>` | class label of an object | GUI and templates |
| `archetype.prop_name.<property>` | label of a property | GUI and templates |
| `archetype.enum_choices.<choice>` | label of an enumeration choice | GUI and templates |
| `archetype.enum_units.<unit>` | label of a unit of a `unitProperty` | GUI and templates |
| `archetype.enum_choices.tooltip.<property>.<choice>` | tooltip of a choice (`valueTooltips="true"`) | GUI |
| `archetype.tooltip.<tooltip>` | tooltip of a property (its `tooltip` attribute) | GUI |
| `archetype.prop_category.<category>` | tab of the edit form | GUI |
| `archetype.category.<category>` | tab of the toolbar (archetype category folder) | GUI |
| `xslt_templates.<template>` | name of a template (view) | GUI |
| `xslt_templates.description.<template>` | description of a template (view) | GUI |
| `xslt.trace_type.<trace type>` | label of a trace type | templates |
| `xslt.<name>` | literal text used by a template | templates |

Punctuation (`:`, brackets, etc.) belongs to the template, not to the label.
The application itself defines some keys in `resources/i18n/<lang>/` that profiles
normally reuse, such as `archetype.class.:proteus-document` or
`archetype.prop_name.:proteus-name`.

Where the strings live
----------------------

```
<profile folder>
  |
  +-- i18n
        |
        +-- languages.xml                   language keys, directories and default
        |
        +-- <lang>                          (e.g. es_es, en_us)
              |
              +-- <archetype labels>.yaml   archetype classes, properties, enums...
              +-- xslt_labels.yaml          labels used only by the templates
              +-- xslt_templates.yaml       names and descriptions of the templates
              +-- <new archetype>.yaml      <-- just add a file here
```

File names are not significant: every YAML file of the language directory is
loaded. Current profiles use these names:

| File | basic | madeja |
| --- | --- | --- |
| archetype labels | `basic_archetypes.yaml` | `archetypes.yaml` |
| template labels | `xslt_labels.yaml` | `xslt_labels.yaml` |
| labels of archetypes not migrated yet | — | `xslt_pending_labels.yaml` |
| template names | `xslt_templates.yaml` | `xslt_templates.yaml` (`xslt_plantillas.yaml` in `es_es`) |

All YAML files in the language directory are merged into a single dictionary,
so **a key must be defined in one file only**: repeated keys silently override
each other in file system order. Inside a single file, YAML also keeps the last
of two repeated keys without any warning.

Adding a new archetype
----------------------

1. Write the archetype XSLT module and include it in `default.xsl`, only if the
   archetype is not rendered by the generic `any_archetype.xsl` template. If the
   archetype has its own stylesheet, `default.css` must import it as well.
2. Add the labels of the new classes, properties, enumeration choices, units,
   tooltips and any literal text used by its template, for every language: in
   the existing YAML files or in a new `<profile>/i18n/<lang>/<archetype>.yaml`.

See `archetype_tasks.md` for the complete list of steps to add an archetype.

Previous design (removed)
-------------------------

Until 2026/09/16 every localized string was an XSLT variable declared in
`i18n/i18n_<lang>.xsl`, included from a per-language entry point
(`default_<lang>.xsl`), and the labels which had to be looked up by name
(classes, properties, enumerations, trace types) were collected in result tree
fragment dictionaries in `labels/*.xsl`, accessed with
`exsl:node-set()`:

```xml
<xsl:variable name="property_labels_dictionary">
  <label key="address"><xsl:value-of select="$proteus:lang_address"/></label>
  ...
</xsl:variable>
<xsl:variable name="property_labels" select="exsl:node-set($property_labels_dictionary)"/>
```

That design had three problems which motivated the change:

* An `xsl:variable` is a single binding, so dictionaries could not be extended
  by an included module: adding an archetype meant editing core files.
* `key()` cannot index a result tree fragment, so every lookup was a linear
  scan and no index could be built.
* A variable referenced but not declared is a compile error, so all language
  files had to be kept exactly in sync (and one string, `lang_synonyms`, was
  in fact missing).
