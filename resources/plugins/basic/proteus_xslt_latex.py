# ==========================================================================
# File: proteus_xslt_latex.py
# Description: XSLT functions for templates that generate LaTeX:
#              - latex_escape: escapes LaTeX special characters in text.
#              - markdown_to_latex: converts Markdown to LaTeX.
#              - latex_url: hyperlink whose text is the URL itself.
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import re
import logging

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import markdown
import lxml.html

# --------------------------------------------------------------------------
# Plugins imports
# --------------------------------------------------------------------------

from basic.glossary_handler import GlossaryHandler

# logging configuration
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# Markdown extensions, the same as generate_markdown except codehilite,
# whose output is HTML-specific
MARKDOWN_EXTENSIONS = [
    "markdown.extensions.fenced_code",
    "markdown.extensions.tables",
]

# Characters with a special meaning in LaTeX. '"', '<' and '>' are also
# escaped because babel makes them active in some languages (e.g. spanish).
LATEX_SPECIAL_CHARACTERS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
    '"': r"\textquotedbl{}",
}

LATEX_SPECIAL_CHARACTERS_PATTERN = re.compile(
    "|".join(re.escape(c) for c in LATEX_SPECIAL_CHARACTERS)
)

# HTML inline elements and their LaTeX equivalents
INLINE_ELEMENTS = {
    "strong": r"\textbf{%s}",
    "b": r"\textbf{%s}",
    "em": r"\emph{%s}",
    "i": r"\emph{%s}",
    "del": r"\sout{%s}",
    "code": r"\texttt{%s}",
}

# Non-breaking space. '~' is avoided because babel makes it active in
# some languages and it breaks inside long tables.
NBSP = r"\nobreakspace{}"


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------


def _xslt_argument_to_text(argument) -> str:
    """
    XSLT arguments may be strings, node-sets (lists of elements or strings)
    or result tree fragments. Return their string value.
    """
    if isinstance(argument, list):
        return "".join(
            item if isinstance(item, str) else "".join(item.itertext())
            for item in argument
        )
    return "" if argument is None else str(argument)


def escape_latex(text: str) -> str:
    """
    Escapes LaTeX special characters in the given plain text.
    """
    return LATEX_SPECIAL_CHARACTERS_PATTERN.sub(
        lambda match: LATEX_SPECIAL_CHARACTERS[match.group()], text
    )


def escape_url(url: str) -> str:
    """
    Escapes an URL to be used as the first argument of \\href. It is read
    almost verbatim, but '%' and '#' must be escaped, and '&' too inside
    tables.
    """
    return url.replace("%", r"\%").replace("#", r"\#").replace("&", r"\&")


def _children_to_latex(element) -> str:
    """
    Converts the text and children of an HTML element to LaTeX.
    """
    result = escape_latex(element.text) if element.text else ""
    for child in element:
        result += _element_to_latex(child)
        if child.tail:
            result += escape_latex(child.tail)
    return result


def _code_block_to_latex(text: str) -> str:
    """
    Converts a code block to LaTeX. Verbatim environments cannot be used
    inside table cells, so the code is escaped and spaces and line breaks
    are kept explicitly.
    """
    lines = [
        escape_latex(line).replace(" ", NBSP) or NBSP
        for line in text.rstrip("\n").split("\n")
    ]
    return "\\begin{proteuscode}\n" + "\\\\\n".join(lines) + "\n\\end{proteuscode}\n\n"


def _table_to_latex(table) -> str:
    """
    Converts an HTML table to a proteusmdtable environment (see proteus.sty).
    """
    rows = table.findall(".//tr")
    if not rows:
        return ""

    columns = max(len(row.findall("./th") + row.findall("./td")) for row in rows)

    result = "\\begin{proteusmdtable}{%s}\n" % ("X" * columns)
    for row in rows:
        cells = []
        for cell in row.findall("./th") + row.findall("./td"):
            text = _children_to_latex(cell)
            cells.append(r"\textbf{%s}" % text if cell.tag == "th" else text)
        result += " & ".join(cells) + " \\\\ \\hline\n"
    return result + "\\end{proteusmdtable}\n\n"


def _element_to_latex(element) -> str:
    """
    Converts an HTML element generated by python-markdown to LaTeX.
    Unknown elements (e.g. raw HTML) are replaced by their content.
    """
    tag = element.tag if isinstance(element.tag, str) else ""

    if tag in INLINE_ELEMENTS:
        return INLINE_ELEMENTS[tag] % _children_to_latex(element)

    if tag == "p":
        return _children_to_latex(element).strip() + "\n\n"

    if tag in ("ul", "ol"):
        environment = "itemize" if tag == "ul" else "enumerate"
        items = "".join(
            "\\item " + _children_to_latex(item).strip() + "\n"
            for item in element.findall("./li")
        )
        return "\\begin{%s}\n%s\\end{%s}\n\n" % (environment, items, environment)

    if tag == "pre":
        return _code_block_to_latex("".join(element.itertext()))

    if tag == "a":
        href = element.get("href", "")
        text = _children_to_latex(element)
        if href.startswith("#"):
            # Internal link, e.g. glossary items (object ids are labels)
            return r"\hyperref[%s]{%s}" % (href[1:], text)
        return r"\href{%s}{%s}" % (escape_url(href), text)

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "\\paragraph*{%s}\n" % _children_to_latex(element).strip()

    if tag == "blockquote":
        return "\\begin{quote}\n%s\\end{quote}\n\n" % _children_to_latex(element)

    if tag == "br":
        return "\\newline\n"

    if tag == "hr":
        return "\\par\\noindent\\rule{\\linewidth}{0.4pt}\\par\n"

    if tag == "table":
        return _table_to_latex(element)

    return _children_to_latex(element)


def markdown_to_latex_string(text: str, glossary_highlight: bool = True) -> str:
    """
    Converts Markdown to LaTeX. Markdown is first converted to HTML with
    python-markdown (as generate_markdown does), glossary items are linked
    using the HTML glossary highlighter (so code blocks are skipped) and
    the HTML tree is then converted to LaTeX.
    """
    if not text.strip():
        return ""

    html: str = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)

    if glossary_highlight:
        html = GlossaryHandler.highlight_glossary_items(None, html)

    root = lxml.html.fragment_fromstring(html, create_parent="div")

    # Newlines between HTML blocks are kept as text: one blank line is enough
    return re.sub(r"\n{3,}", "\n\n", _children_to_latex(root)).strip()


# --------------------------------------------------------------------------
# XSLT functions
# --------------------------------------------------------------------------


def latex_escape(context, text) -> str:
    """
    XSLT function: escapes LaTeX special characters in the given text.
    """
    return escape_latex(_xslt_argument_to_text(text))


def markdown_to_latex(context, text, glossary_highlight=True) -> str:
    """
    XSLT function: converts the given Markdown text to LaTeX. Glossary items
    are linked to their definitions unless glossary_highlight is false.
    """
    try:
        return markdown_to_latex_string(
            _xslt_argument_to_text(text), bool(glossary_highlight)
        )
    except Exception as e:
        log.error(f"Error converting Markdown to LaTeX: {e}")
        return escape_latex(_xslt_argument_to_text(text))


def latex_url(context, url) -> str:
    """
    XSLT function: hyperlink to the given URL whose text is the URL itself.
    """
    url = _xslt_argument_to_text(url).strip()
    return r"\href{%s}{\texttt{%s}}" % (escape_url(url), escape_latex(url))
