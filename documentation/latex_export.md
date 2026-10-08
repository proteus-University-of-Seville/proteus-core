LaTeX and PDF (from LaTeX) export
=================================

Besides the HTML views, a profile may include **LaTeX templates**: XSLT templates whose
output is a LaTeX document instead of HTML. They are not views; they are used by two export
formats of the basic plugin:

* **LaTeX (with resources folder)** (`latex`): writes `main.tex` and its resources in a new
  folder, ready to be edited or compiled by the user.
* **PDF (from LaTeX)** (`pdf_latex`): writes the same sources in a temporary folder,
  compiles them with a LaTeX engine installed in the system and saves the PDF.

Default names are built from the acronym of the current document, or its name if it has
none (`document_file_name` in `basic/export/file_names.py`), so that every format can be
exported to the same folder without collisions:

* HTML and LaTeX folders: `<acronym>-exported-html`, `<acronym>-exported-latex`.
* PDF files: `<acronym>_html.pdf` (PDF from HTML), `<acronym>_latex.pdf` (PDF from LaTeX),
  see `FILE_NAME_SUFFIX` of each strategy.

The basic profile ships one LaTeX template, `profiles/basic/xslt/latex`, the counterpart of
the `default` view. It renders the current document like the HTML view (cover, table of
contents, sections, paragraphs, comments, glossary and bibliography items, figures, symbolic
links, property cards with icons and accent colours, traceability matrices) and it is
translated with the same i18n files.


Requirements
------------

* Both formats are only listed in the export dialog if the current profile has a LaTeX
  template (`ExportStrategy.is_available`). A profile created from basic does not have one
  unless it copies `xslt/latex` (madeja has its own, see below).
* PDF export needs `xelatex`, `lualatex` or `pdflatex` in the `PATH` (MiKTeX or TeX Live).
  The export form lists the engines found in that order, `xelatex` by default; if there is
  none, the format shows an error and cannot be used. xelatex and lualatex support any
  Unicode character (a character the font does not have is left out, with a `Missing
  character` warning in the log), while pdflatex fails with characters it does not know
  (e.g. arrows or emojis in the texts of the project); xelatex is faster than lualatex.
  LaTeX export does not need any engine.
* `latexmk` is not used: MiKTeX on Windows does not ship the Perl interpreter it needs. The
  export does what it would do: the engine is run until the auxiliary files (`main.aux`,
  `main.toc`, `main.out`) do not change in a pass and the log does not ask for another one
  (`Rerun to get...`, `Label(s) may have changed`), at least twice and at most four times
  (`LATEX_MIN_PASSES`, `LATEX_MAX_PASSES`). Usually two passes are enough; a third one is
  needed when the second changes page numbers (e.g. a table of contents longer than one
  page with `twoside`).
* The generated document needs these packages: babel, fontspec (xelatex/lualatex) or
  fontenc+lmodern (pdflatex), geometry, xcolor, graphicx, array, xltabular, changepage,
  amssymb, ulem, float, adjustbox, tcolorbox, enumitem, caption, hyperref. MiKTeX installs
  missing packages on the fly; the first compilation may take a minute, and if MiKTeX is
  configured to *ask* before installing packages, its dialog appears during the export.
* If the compilation fails, the LaTeX log is copied next to the selected PDF file
  (`<name>.log`).
* Remote figures are downloaded during the export, so it needs network access to show them
  (15 seconds of timeout per image).


Document layout
---------------

* Class `article` with options `12pt,a4paper,twoside,titlepage`. With `twoside` the cover,
  the table of contents and the body start on odd pages (`\cleardoublepage`), and
  `\raggedbottom` avoids the stretched vertical space of `\flushbottom`.
* Fonts: Latin Modern with every engine, and the sans serif family for the whole document
  (`\familydefault` is `\sfdefault`); code uses the typewriter family.
* Tables (property cards, Markdown tables and traceability matrices) are centred, 95% of the
  text width (`\ProteusTableFraction` in `proteus.sty`), with rows separated by
  `\arraystretch` 1.5. Columns of Markdown tables are left-aligned. The content of the value
  column of cards (`Q`) and of the columns of Markdown tables (`Y`) is set in a top-aligned
  `minipage` (`\proteus@cellbegin`, `\proteus@cellend`): cells of X columns start in
  horizontal mode, so a list at the beginning of a cell would end that empty paragraph and
  leave an empty line above it. The minipage starts lists without space above and removes the
  space after a final list; the cell ends with the depth of the row strut
  (`\proteus@finalstrut`) and paragraphs inside cells keep the `\parskip` of the document.
* Cards have `\medskipamount` above and below (`\LTpre`, `\LTpost`): 12pt between two cards,
  while headings after a card keep their usual space.


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
remote/image-<n>.<ext>       remote figures, downloaded
```

Assets are found by looking for `{assets/<file>}` in `main.tex`, so templates must always
reference them that way. Formats that LaTeX cannot include (GIF, BMP, WebP, SVG, TIFF, ICO)
are converted to PNG (`<file>.png`) and the reference is updated.

Remote figures (`url` property) are written by the template as
`\ProteusRemoteImage{<width>}{<URL>}`, with the URL unescaped. The export strategies
download each URL once and replace the command by `\includegraphics` (PNG, JPEG and PDF are
kept as they are, other formats Qt can read are converted to PNG), or by
`\ProteusMissingImage{<link>}` if the image cannot be downloaded: a box with the text of the
i18n key `xslt.remote_figure_not_available` and the URL.

The sources are written in two steps. `prepare_latex_sources` renders the document and copies
resources, icons and assets in the application thread, because rendering uses the project and
plugin components. `finish_latex_sources` downloads the remote figures and writes `main.tex`;
the export strategies run it in a `LaTeXSourcesTask` (a `QRunnable` of the global
`QThreadPool`), so the application keeps responding during the downloads, and continue (or
start the compilation) when its `finished` signal arrives. `write_latex_sources` runs both
steps in the calling thread, for scripts.

Closing the export dialog while an export is running cancels it (`ExportDialog.done` calls
`ExportStrategy.cancel`, which does nothing by default). Both LaTeX strategies stop what is
running and remove their partial output without emitting `exportFinishedSignal`:

* While the sources are being written, `LaTeXSourcesTask.cancel` makes the task stop before
  the next download and remove the folder itself. If the task had already finished, it
  returns `False` and the strategy removes the folder.
* While compiling, the engine process (a child of the strategy) is killed and the temporary
  folder is removed once it has exited.

The export format cannot be changed while an export is running.


Bibliography and citations
--------------------------

Bibliography items are LaTeX bibliography entries, without BibTeX:

* Each one is written as `\ProteusBibItem[<name>]{<id>} <authors>. <details>` (a `\bibitem`
  with the item name as label, as in the HTML view). Consecutive items share one
  `proteusbibliography` list, a `thebibliography` without its own heading (the items are
  already in a section of the document) and with hanging labels as wide as needed. The list
  stays where the items are in the document, in their order.
* Citations are `\cite{<id>}`, printed as `[<name>]`:
  * In Markdown texts: bibliography items are also glossary items, so the glossary
    highlighter links their names; links to bibliography items of the rendered document are
    converted to `\cite` (`markdown_to_latex` receives their ids, see the `bibliography_ids`
    variable in `core/utilities.xsl`). Brackets written around the name
    (`[Wiegers and Beatty 2013]`) are removed, since `\cite` adds them.
  * In traces: a trace to a bibliography item of the document (e.g. *Dependencies*) is
    `\cite{<id>}` (`trace_target` in `core/properties.xsl`).
  * Bibliography items of other documents are not cited: links and traces to them are plain
    text, like any other object of another document.
* A bibliography item shown by a symbolic link opens and closes its own list (the `standalone`
  parameter passed by `symbolic_link.xsl`), and `\ProteusBibItem` does not define the
  citation again inside the link.
* No extra tool or compilation pass is needed: the two passes resolve the citations.

A `.bib` file processed by BibTeX or biber would need structured bibliography items (entry
type, title, year, publisher...), which the basic profile does not have.


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
  (`label & value \\ \hline`). A long table steps the `table` counter: `\end{xltabular}` must
  be followed by `\ProteusCardEnd`, which restores it, so that only real tables (e.g.
  traceability matrices) are numbered.
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
needs a LaTeX module too; archetypes without one use the generic property card. Changes to
the core of the template (`core/*.xsl`, `proteus.sty`) must be made in every copy.

The madeja profile (`C:\proteus-profiles\madeja`, its own repository) has a copy of the basic
template plus:

* the accent colours of its archetypes in `proteus.sty`, taken from its CSS files;
* `unitProperty` in `core/properties.xsl` (`<value> <unit>`), as in its HTML template;
* `archetypes/requirements/information_requirement.xsl`: specific data as a list in a row
  after the description;
* `archetypes/requirements/use_case.xsl`: the evolved use case. The HTML card has a third
  column for step numbers and a label spanning the rows of a sequence (`rowspan`); here every
  step, branch step, exception action and ending is a row of the card, so that long
  sequences break across pages. The label is written in the first row only, the rows of a
  sequence are separated by `\cline{2-2}`, and the value cell shows the number and the action
  with `\ProteusStepHeader`, `\ProteusStep` and `\ProteusSubStep` (madeja's `proteus.sty`).

Anchors (`\ProteusAnchor`, i.e. `\phantomsection`) at the beginning of a minipage or of a list
item must come after `\leavevmode`: in vertical mode they add an empty first line.


Known limitations
-----------------

* Linked copies of figures and matrices (symbolic links) get a new number.
* Sections placed after an appendix are numbered with letters (appendices can only be placed
  directly in a document, at the end).
* Raw HTML in Markdown is dropped (its text is kept).
