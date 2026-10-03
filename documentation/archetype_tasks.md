Creating a new object archetype
===============================

An object archetype is the template Proteus clones when the user creates an object
(a section, a requirement, a use case step...). Archetypes belong to a **profile**
(e.g. `profiles/basic`, or an external profile such as madeja). This document lists the
files to create and the files to modify to add one. See `PROJECT_STORAGE_MANUAL.md` for
the XML format of objects and properties, and `i18n_design.md` for the translations.

Profiles ship **one complete archetype set per language** (see
`archetypes/languages.xml`). Every step below that touches `archetypes/` or `i18n/` must be
done for **every language**: the sets must keep the same IDs, classes and properties, only
texts change.

Summary of the files involved (`<lang>` is e.g. `en_us`, `es_es`; `<main-class>` is the
last class of the archetype; `<id_>` is its ID with underscores):

| File | Action | Step |
| --- | --- | --- |
| `archetypes/<lang>/objects/NN_<category>/objects/<id>.xml` | create | 1, 2 |
| `archetypes/<lang>/objects/NN_<category>/objects.xml` | modify | 1 |
| `archetypes/<lang>/objects/NN_<category>/assets/<file>` | create, if needed | 3 |
| `icons/<main-class>.png` | create | 4 |
| `i18n/<lang>/*.yaml` | modify | 5 |
| `xslt/<template>/archetypes/<category>/<id_>.xsl` | create, if needed | 6 |
| `xslt/<template>/default.xsl` | modify, if a module was created | 6 |
| `xslt/<template>/resources/css/<id_>.css` and `default.css` | create and modify, optional | 7 |
| other archetypes that must accept or trace the new one | modify, if needed | 2 |


1. Create the archetype file and declare it
-------------------------------------------

```
<profile folder>
  |
  +-- archetypes
        |
        +-- languages.xml
        |
        +-- <lang>                              (en_us, es_es, ...)
              |
              +-- objects
                    |
                    +-- <NN_category>           (e.g. 00_general, 02_requirements)
                          |
                          +-- objects.xml
                          |
                          +-- objects
                          |     |
                          |     +-- <archetype id>.xml
                          |
                          +-- assets
                                |
                                +-- <archetype assets>
```

* The archetype file is `objects/<archetype id>.xml`, and its `id` attribute must be the
  file name without extension. IDs must be unique in the profile.
* Each category folder is a tab of the creation toolbar. `NN` (two digits) orders the
  tabs, and the rest of the name after `NN_` is the category key, translated as
  `archetype.category.<category>` (e.g. `02_requirements` → `requirements`). A category
  folder can only contain `objects.xml`, `objects/` and `assets/`.
* **Declare the archetype in `objects.xml`**: `<object id="<archetype id>" />`.
  This file is **mandatory**: Proteus loads *only* the archetypes listed in it, in that
  order, which is the order of the buttons in the tab. An archetype file that is not
  listed does not exist for Proteus.
* *Second-level archetypes*, i.e. archetypes that only accept specific parents (such as use
  case steps), must be listed too, otherwise they cannot be created. They get a toolbar
  button like any other archetype: buttons are enabled only when the selected object
  accepts the archetype as a child, so they are disabled until a valid parent is selected.

**Alternative**: with the developer features enabled, an existing object can be stored as
an archetype from its context menu. Proteus then writes the object (and its descendants)
into the category folder of the **current language only**, appends it to `objects.xml` and
copies its assets. The stored files keep the object's random 12-character ID and its
current values, so rename the file and the `id` (in `objects.xml` too), clean the values,
and repeat the archetype for the other languages. Steps 4 to 7 are still needed.


2. Write the archetype XML
--------------------------

```xml
<?xml version="1.0" encoding="UTF-8"?>
<object
    id="use-case"
    classes="software-requirement use-case"
    acceptedChildren="use-case-step conditional-branch"
    acceptedParents=":Proteus-document section"
>
  <properties>
    <codeProperty name=":Proteus-code" category="general" inmutable="true">
      <prefix><![CDATA[UC-]]></prefix>
      <number>001</number>
      <suffix><![CDATA[]]></suffix>
    </codeProperty>
    <stringProperty name=":Proteus-name" category="general" tooltip="use-case-name">Concrete use case</stringProperty>
    <dateProperty name=":Proteus-date">2024-10-01</dateProperty>
    <markdownProperty name="description" category="detail"><![CDATA[The system shall ... when _[triggering event]_.]]></markdownProperty>
    ...
    <markdownProperty name="comments" category="comments"><![CDATA[]]></markdownProperty>
  </properties>

  <children numbered="true">
  </children>
</object>
```

Rules:

* `classes` lists class tags from the most general to the most specific. **The last one is
  the main class**, which determines:
  * the toolbar button: archetypes with the same main class are grouped in one button as
    variants of the same class (e.g. `use-case` and `abstract-use-case`, both with main
    class `use-case`); give the archetype its own main class to get its own button;
  * the icon (`icons/<main-class>.png`, step 4);
  * the class label in the toolbar and in the rendered document
    (`archetype.class.<main-class>`, step 5);
  * the CSS class of its table in the rendered document (step 7).
* Class tags do not need an archetype of their own: *abstract* classes (e.g.
  `traceable-object`, `use-case-step`) model generalizations and are used in
  `acceptedChildren`, `acceptedParents`, `acceptedTargets` and in the XSLT templates to
  match families of archetypes.
* A child is accepted only if the parent's `acceptedChildren` contains `:Proteus-any` or
  one of the child's classes, **and** the child's `acceptedParents` (default
  `:Proteus-any`) contains one of the parent's classes. Use both sides to forbid unwanted
  nesting. If the new archetype must be accepted by existing archetypes, or be the target of
  their traces, update their `acceptedChildren` or `acceptedTargets` as well.
* The order of the properties is the order of the fields in the edit form and in the
  generic rendering. `category` (default `general`) selects the form tab; a new category
  needs the label `archetype.prop_category.<category>`.
* Default values are the starting point of every new object. Linguistic patterns can be
  given as default text with placeholders in italics (e.g. `when _[triggering event]_`),
  with a `tooltip` explaining what to replace. When two variants of an object differ in the
  pattern, create one archetype per variant.
* `:Proteus-code` (`codeProperty`, usually `inmutable="true"`) gives automatic codes: the
  number is incremented on creation from the biggest code with the same prefix.
* Children declared in the archetype are created with it: inside `<children>`, an element
  with the ID of a sibling archetype file (e.g. `<object id="specific-data"/>`) adds a copy
  of that archetype as a child of every new object.
* Every object created from the archetype keeps **its own copy** of the archetype's
  classes and property definitions. Changing an archetype later does not change existing
  objects, and objects do not record which archetype they come from: implement behaviour
  with classes or properties (e.g. an `is-abstract` boolean), not with the archetype ID.


3. Assets
---------

If a `fileProperty` of the archetype has a default file (e.g. a logo or a photo), put the
file in the `assets/` folder of the category. It is copied into the project's `assets/`
when an object is created.


4. Icon
-------

Create `icons/<main-class>.png` in the profile, 48x48 pixels, in the flat style of the
profile icons. Proteus finds it by name; `icons/icons.xml` is only needed to override
other icons (application, menus, documents). Without an icon, a default one is used.


5. i18n labels for the UI and the XSLT templates
------------------------------------------------

Create the labels for the new archetype in the YAML files of every
**&lt;profile&gt;/i18n/&lt;lang&gt;** folder (the profile's archetype labels file is
`basic_archetypes.yaml` in the basic profile and `archetypes.yaml` in madeja; a new YAML
file can be added too).

**NOTE**: all YAML files in a language folder are merged into a single dictionary. A key
must be defined in **one** file only: a key defined in two files silently overrides
itself. Keys are lowercase (lookups are case-insensitive); write values between quotes;
`\n` in a class label breaks the toolbar button text.

Labels shared by the GUI and the templates:

* archetype.category.&lt;category name&gt; — only for a new category folder
* archetype.class.&lt;class name&gt; — for **every** class tag used by the archetype,
  including abstract classes (they are shown in class lists, e.g. when configuring a
  traceability matrix)
* archetype.prop_category.&lt;property category name&gt; — only for a new form tab
* archetype.prop_name.&lt;property name&gt;
* archetype.enum_choices.&lt;enum choice&gt;
* archetype.enum_choices.tooltip.&lt;property name&gt;.&lt;enum choice&gt; — only for
  `enumProperty` with `valueTooltips="true"`
* archetype.enum_units.&lt;unit&gt; — units of `unitProperty`
* archetype.tooltip.&lt;tooltip info name&gt;

Names used exclusively by the templates:

* xslt.trace_type.&lt;trace type name&gt;
* xslt.&lt;literal text name&gt; — usually in `xslt_labels.yaml`; labels of archetypes not
  migrated yet are kept in `xslt_pending_labels.yaml` and must be moved out of it when they
  are used

Reuse existing keys when the label is the same (e.g. `archetype.prop_name.description`).
Missing keys are shown as `!key!` in the rendered document and as the raw name or the key
in the GUI. See **documentation/i18n_design.md** for the details of the XSLT i18n design.


6. XSLT rendering
-----------------

By default an object is rendered by `archetypes/any_archetype.xsl` as a table with one row
per non-empty property (empty text and enumerations set to `tbd` are not shown). A
specific module is only needed to change that, e.g. to reorder rows, to render children in
a custom way or to hide other "empty" values (madeja's use case hides a frequency of `0`):

1. Create `xslt/<template>/archetypes/<category>/<id_>.xsl`, matching the archetype by
   class with priority 1 (subclasses use higher priorities and may call the superclass
   template by name):

   ```xml
   <xsl:template
     match="object[contains(concat(' ', normalize-space(@classes), ' '),' use-case ')]"
     name="use_case_template"
     priority="1"
   >
     <xsl:call-template name="generate_table">
       <xsl:with-param name="excluded_properties" select="',:Proteus-name,:Proteus-code,:Proteus-date,version,authors,sources,'"/>
     </xsl:call-template>
   </xsl:template>
   ```

2. Include it in `xslt/<template>/default.xsl`, in the block of its category:
   `<xsl:include href="archetypes/<category>/<id_>.xsl" />`.

Useful named templates of `core/`:

* `generate_table` (`core/generate_table.xsl`): the object card. Parameters:
  `excluded_properties` and `included_properties` (comma-delimited lists, e.g.
  `',a,b,'`), `span` (value columns), `extra_rows_before` (custom rows inserted before the
  property rows, built in a variable), `extra_rows` (rows instead of the nested children),
  `show_children`, `postfix` (text after the name in the header), `image` (corner image).
* `generate_property_row` (`core/utilities.xsl`): one row for a property.
* `generate_markdown` (`core/utilities.xsl`): Markdown to HTML; a single paragraph is not
  wrapped in `<p>`, so it can be inlined in a sentence.
* Property types are rendered by the templates of `core/properties.xsl`
  (`traceProperty`, `enumProperty`, `unitProperty`, `fileProperty`, ...). A more specific
  match pattern in an archetype module overrides them for one property of one archetype.

Literal texts come from `proteus-utils:i18n('xslt.<name>')`; extra arguments of that
function are `{0}` format arguments, not a fallback text.


7. Choose a colour for the archetype
------------------------------------

Objects are rendered as a framed card with a coloured left edge, a tinted header row and a
pill holding the archetype icon and name. All of that is derived from a single custom
property, so the stylesheet of a new archetype is one rule using its **main class**:

```css
.proteus_table.<main-class> {
  --accent: #0e7490;
}
```

Put it in **&lt;template&gt;/resources/css/&lt;id_&gt;.css** and add an `@import` to
**default.css**. Archetypes which do not declare an accent fall back to a neutral slate
colour (`#475569`), so this step is optional.

Each profile has its own palette. The basic profile uses `#0e7490` teal (organizations),
`#6d28d9` violet (stakeholders), `#83900e` olive (meetings) and `#4f46e5` indigo
(traceability matrices). Madeja uses the Material colours of its icons, e.g. `#00ACC1`
(use cases), `#26A69A` (general requirements), `#00897B` (functional requirements),
`#455A64` (actors and modelling), `#5C6BC0`/`#7E57C2` (business analysis) and
`#C62828`/`#E53935` (defects and conflicts).

The density of the rows is set in **proteus_table.css** by `--pad-y` and `--line-height`,
which apply to every archetype. Rules for custom rows must be at least as specific as the
generic cell rule (`table.proteus_table > tbody > tr > td`) to override it.


8. Check the result
-------------------

Proteus loads the profile at start-up, so restart it after changing the profile. Then:

* The archetype appears in its tab, in the right position, with its icon and label, in
  every language, and its button is enabled exactly when a valid parent is selected.
* The edit form shows the properties in the expected tabs, with labels and tooltips.
* The rendered document shows no `!key!` and no XSLT errors (logged as CRITICAL).

The archetypes can also be checked from a script with the Proteus Python environment:
`ArchetypeRepository.load_object_archetypes(<profile>/archetypes/<lang>)` returns the
toolbar tabs and buttons, and `parent.accept_descendant(child)` tells whether an archetype
is accepted as a child of another.
