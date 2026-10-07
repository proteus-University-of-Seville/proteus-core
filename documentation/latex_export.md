LaTeX and PDF (through LaTeX) export
====================================

Besides the HTML views, a profile may include **LaTeX templates**: XSLT templates whose
output is a LaTeX document instead of HTML. They are not views; they are used by two export
formats of the basic plugin:

* **LaTeX (with resources folder)** (`latex`): writes `main.tex` and its resources in a new
  folder, ready to be edited or compiled by the user.
* **PDF file (through LaTeX)** (`pdf_latex`): writes the same sources in a temporary folder,
  compiles them with a LaTeX engine installed in the system and saves the PDF.

The basic profile ships one LaTeX template, `profiles/basic/xslt/latex`, the counterpart of
the `default` view. It renders the current document like the HTML view (cover, table of
contents, sections, paragraphs, comments, glossary and bibliography items, figures, symbolic
links, property cards with icons and accent colours, traceability matrices) and it is
translated with the same i18n files.


Requirements
------------

* PDF export needs `xelatex`, `lualatex` or `pdflatex` in the `PATH` (MiKTeX or TeX Live).
  The export form lists the engines found; if there is none, the format shows an error and
  cannot be used. LaTeX export does not need any engine.
* `latexmk` is not used: MiKTeX on Windows does not ship the Perl interpreter it needs. The
  engine is run twice, enough for the table of contents and cross-references.
* The generated document needs these packages: babel, fontspec (xelatex/lualatex) or
  fontenc+lmodern (pdflatex), geometry, xcolor, graphicx, array, xltabular, changepage,
  amssymb, ulem, float, adjustbox, tcolorbox, enumitem, caption, hyperref. MiKTeX installs
  missing packages on the fly; the first compilation may take a minute, and if MiKTeX is
  configured to *ask* before installing packages, its dialog appears during the export.
* If the compilation fails, the LaTeX log is copied next to the selected PDF file
  (`<name>.log`).


How it works
------------

| Piece | File |
| --- | --- |
| Output format of a template: `<template name="latex" output="latex">` (default `html`) | `proteus/model/template.py` (`Template.output_format`, `is_view`) |
| Only HTML templates are views (views menu, default view, settings) | `Controller.get_available_xslt`, `ProfileSettings._validate_profile_basic_content` |
| Templates of a given format, rendering with any template | `Controller.get_templates_by_output_format`, `Controller.render_template` |
| Text output (`<xsl:output method="text">`) is serialized as text | `RenderService.render` |
| XSLT functions `latex_escape`, `markdown_to_latex`, `latex_url` | `resources/plugins/basic/proteus_xslt_latex.py` |
| Export strategies `latex` and `pdf_latex` | `resources/plugins/basic/export/export_latex.py` |
| LaTeX template of the basic profile | `profiles/basic/xslt/latex/` |
| Style of the generated document (counterpart of `default.css`) | `profiles/basic/xslt/latex/resources/proteus.sty` |

Export folder layout (also the temporary folder compiled for PDF):

```text
main.tex
resources/proteus.sty        template files except *.xsl and *.xml
resources/images/logo_us.png
icons/<main-class>.png       profile icons
assets/<file>                project assets referenced in main.tex
```

Assets are found by looking for `{assets/<file>}` in `main.tex`, so templates must always
reference them that way. Formats that LaTeX cannot include (GIF, BMP, WebP, SVG, TIFF, ICO)
are converted to PNG (`<file>.png`) and the reference is updated. Remote figures (`url`
property) are shown as a link, not downloaded.


Writing LaTeX templates and modules
-----------------------------------

The LaTeX template has the same structure as `default`: `latex.xsl` includes `core/*.xsl` and
one module per archetype, and the core named templates keep the same names and parameters
(`generate_table`, `generate_property_row`, `generate_markdown`), so porting an archetype
module is mostly replacing HTML by LaTeX. Rules:

* **Escape every text** taken from the project or from the i18n files: named templates
  `tex` (`proteus-utils:latex_escape`) and `label` (`latex_escape(i18n(key))`). Unlike
  HTML, the built-in text template cannot be used: `core/properties.xsl` has a low-priority
  `properties/*` template that escapes any property without a more specific template.
* **Markdown** goes through `generate_markdown`, which calls
  `proteus-utils:markdown_to_latex(text, glossary-highlight)`: Markdown is converted to HTML
  with python-markdown (same extensions as the HTML view except `codehilite`), glossary items
  are linked with the HTML glossary highlighter, and the HTML is converted to LaTeX (emphasis,
  code, lists, links, tables as `proteusmdtable`, code blocks as `proteuscode`, quotes,
  rules). Code blocks are not verbatim, so they also work inside table cells.
* **Labels and links** use the object ids: `\ProteusAnchor{id}` (named template `anchor`) for
  objects and `\ProteusLabel{id}` after `\section`, `\caption`...; links are
  `\hyperref[id]{text}`. Both commands do nothing inside symbolic links, which render the
  linked objects again. Traces to objects of other documents are plain text.
* Write `\nobreakspace{}` instead of `~`, and do not write raw `"`, `<` or `>`: babel makes
  them active in some languages (e.g. Spanish) and they break inside long tables.
* **Property cards** (`generate_table`) are `xltabular` long tables that break across
  pages and repeat their header row. Long tables cannot be nested in table cells or placed in
  boxes, so children are rendered below the card, indented (`adjustwidth`), and symbolic
  links are an indented block, not a box. `extra_rows_before` and `extra_rows` are LaTeX rows
  (`label & value \\ \hline`).
* **Accent colours**: `\ProteusSetAccent{<main-class>}{<HTML colour>}` in `proteus.sty`
  (the counterpart of `--accent` in the CSS files).
* **Sections, figures and tables** are numbered by LaTeX; figures and matrices are not
  floating (`[H]`), so they stay where they are in the document, as in the HTML view.
* **Language**: babel's language option is the i18n key `xslt.latex_babel_language`
  (`english`, `spanish`) of the profile's `xslt_labels.yaml`.
* **Template name** shown in the export form: `xslt_templates.<template>` and
  `xslt_templates.description.<template>`.

Profiles are copies, not extensions: a profile created from basic (e.g. madeja) gets the
LaTeX template only if it copies `xslt/latex`, and every archetype with a custom HTML module
needs a LaTeX module too; archetypes without one use the generic property card.


Known limitations
-----------------

* Linked copies of figures and matrices (symbolic links) get a new number.
* Sections placed after an appendix are numbered with letters (appendices can only be placed
  directly in a document, at the end).
* Raw HTML in Markdown is dropped (its text is kept).
* Remote figures are not downloaded.
