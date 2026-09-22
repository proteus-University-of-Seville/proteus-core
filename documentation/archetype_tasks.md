Creating a new object archetype
===============================

Create archetype file and assets
--------------------------------

**&lt;archetype&gt;**.xml is XML file containing the archetype.

The tasks are the following:

1. Declare the new archetype in the **objects.xml** file inside the category folder. The archetype will appear in the tab corresponding to the category in the order specified in the **objects.xml** file.

1. If the archetype needs any assets, e.g. a graphic file, put them in the **assets** directory.

**NOTE**: _Second-level archetypes_, e.g., objects that only accept specific classes of objects as parents (apart from _:Proteus-document_), such as use case steps, must also be declared in the **objects.xml** file.

**Q**: considering that all XML files in the _objects_ directory are going to be processed, is the **objects.xml** file actually necessary?

**A**: The **objects.xml** file is used to specify the order of the archetypes in the category tab of the creation toolbar. Second-level objects are ignored for that purpose.

**Q**: Then, why include second-level objects in the **objects.xml** file?

**A**: I don't know.

```
<profile folder>
  |
  +-- archetypes
        |
        +-- objects
              |
              +-- <99_archetype category>
                    |
                    +-- objects
                    |     |
                    |     +-- <archetype>.xml
                    |
                    +-- assets
                    |     |
                    |     +-- <archetype assets>
                    |
                    +-- objects.xml
```

Create i18n labels for the UI and the XSLT templates
----------------------------------------------------

Create i18n-ed labels for the new archetype in any YAML file in the **&lt;profile&gt;/i18n/&lt;lang&gt;** folders.

**NOTE**: usual names are already created for previous archetypes. If a new YAML file is going to be created for the new archetype, ensure that only new names are included. All YAML files in a language folder are merged into a single dictionary, so a name defined in two files silently overrides itself.

* archetype.category.&lt;category name&gt;
* archetype.class.&lt;class name&gt;
* archetype.prop_category.&lt;property category name&gt;
* archetype.enum_choices.&lt;enum choice&gt;
* archetype.tooltip.&lt;tooltip info name&gt;
* archetype.prop_name.&lt;property name&gt;

Class labels, property labels and enumeration choices are also used by the XSLT templates to render the archetype, so they are written only once. Names used exclusively by the templates are:

* xslt.trace_type.&lt;trace type name&gt;
* xslt.&lt;literal text name&gt;

See **documentation/i18n_design.md** for the details of the XSLT i18n design.

Choose a colour for the archetype
---------------------------------

Objects are rendered as a framed card with a coloured left edge, a tinted header row and a pill holding the archetype icon and name. All of that is derived from a single custom property, so the stylesheet of a new archetype is one rule:

```css
.proteus_table.<class name> {
  --accent: #0e7490;
}
```

Put it in **&lt;template&gt;/resources/css/&lt;archetype&gt;.css** and add an `@import` to **default.css**. Archetypes which do not declare an accent fall back to a neutral slate colour, so this step is optional.

Colours currently in use: `#0e7490` teal (organizations, meetings), `#6d28d9` violet (people), `#1d4ed8` blue (requirements), `#15803d` green (business analysis), `#475569` slate (modelling), `#be123c` rose (management).

The density of the rows is set in **proteus_table.css** by `--pad-y` and `--line-height`, which apply to every archetype.
