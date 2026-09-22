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
(`{0}` placeholders), as in the rest of the application.

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
`:Proteus-date` and `:proteus-date` are the same key. Keys in the YAML files
must therefore be written in lowercase.

Key conventions
---------------

| Key | Content | Shared with the GUI |
| --- | --- | --- |
| `archetype.class.<class>` | class label of an object | yes |
| `archetype.prop_name.<property>` | label of a property | yes |
| `archetype.enum_choices.<choice>` | label of an enumeration choice | yes |
| `xslt.trace_type.<trace type>` | label of a trace type | no |
| `xslt.<name>` | literal text used by a template | no |

Punctuation (`:`, brackets, etc.) belongs to the template, not to the label.

Where the strings live
----------------------

```
<profile folder>
  |
  +-- i18n
        |
        +-- languages.xml
        |
        +-- <lang>                          (e.g. es_es, en_us)
              |
              +-- basic_archetypes.yaml     archetype classes, properties, enums
              +-- xslt_labels.yaml          labels used only by the templates
              +-- xslt_pending_labels.yaml  labels of archetypes not migrated yet
              +-- <new archetype>.yaml      <-- just add a file here
```

All YAML files in the language directory are merged into a single dictionary,
so **a key must be defined in one file only**: repeated keys silently override
each other in file system order.

Adding a new archetype
----------------------

1. Write the archetype XSLT module and include it in `default.xsl` (the only
   file of the template that has to be modified, and only if the archetype is
   not rendered by the generic `any_archetype.xsl` template).
2. Create `<profile>/i18n/<lang>/<archetype>.yaml` for every language with the
   labels of the new class, its properties, its enumeration choices and any
   literal text used by its template.

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
