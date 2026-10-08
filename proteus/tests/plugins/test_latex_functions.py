# ==========================================================================
# File: test_latex_functions.py
# Description: pytest file for the XSLT functions of the basic plugin used
#              by LaTeX templates (resources/plugins/basic/proteus_xslt_latex.py)
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest
import lxml.etree as ET

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

PLUGIN_DIR = Path("resources/plugins").resolve()
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from basic.proteus_xslt_latex import (  # noqa: E402
    escape_latex,
    markdown_to_latex_string,
    latex_escape,
    markdown_to_latex,
    latex_url,
)


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("plain text", "plain text"),
        ("50% & $3", r"50\% \& \$3"),
        ("#tag a_b {x}", r"\#tag a\_b \{x\}"),
        ("~^\\", r"\textasciitilde{}\textasciicircum{}\textbackslash{}"),
        ('<a> "q"', r"\textless{}a\textgreater{} \textquotedbl{}q\textquotedbl{}"),
        ("ñ €", "ñ €"),
    ],
)
def test_escape_latex(text, expected):
    """
    LaTeX special characters are escaped, other characters are kept.
    """
    assert escape_latex(text) == expected


@pytest.mark.parametrize(
    "markdown, expected",
    [
        ("", ""),
        ("**bold** and *emph*", r"\textbf{bold} and \emph{emph}"),
        ("`a_b & c`", r"\texttt{a\_b \& c}"),
        ("- one\n- two", "\\begin{itemize}\n\\item one\n\\item two\n\\end{itemize}"),
        ("1. one\n2. two", "\\begin{enumerate}\n\\item one\n\\item two\n\\end{enumerate}"),
        ("[web](https://a.org/?x=1&y=%20#f)", r"\href{https://a.org/?x=1\&y=\%20\#f}{web}"),
        ("[term](#abc123)", r"\hyperref[abc123]{term}"),
        ("first\n\nsecond", "first\n\nsecond"),
    ],
)
def test_markdown_to_latex_string(markdown, expected):
    """
    Markdown elements are converted to their LaTeX equivalents.
    """
    assert markdown_to_latex_string(markdown, glossary_highlight=False) == expected


def test_markdown_code_block():
    """
    Code blocks keep spaces and line breaks and are escaped, since verbatim
    environments cannot be used inside table cells.
    """
    result = markdown_to_latex_string("```\nif a:\n  b = {}\n```", glossary_highlight=False)

    assert result.startswith("\\begin{proteuscode}")
    assert result.endswith("\\end{proteuscode}")
    assert r"if\nobreakspace{}a:\\" in result
    assert r"\nobreakspace{}\nobreakspace{}b\nobreakspace{}=\nobreakspace{}\{\}" in result


def test_markdown_table():
    """
    Markdown tables are converted to proteusmdtable environments.
    """
    result = markdown_to_latex_string("| A | B |\n|---|---|\n| 1% | 2 |", glossary_highlight=False)

    assert result.startswith("\\begin{proteusmdtable}{YY}")
    assert r"\textbf{A} & \textbf{B} \\ \hline" in result
    assert r"1\% & 2 \\ \hline" in result


def test_xslt_functions_accept_node_sets():
    """
    XSLT functions accept strings and node-sets, as lxml passes them.
    """
    element = ET.fromstring("<markdownProperty>**50%**</markdownProperty>")

    assert latex_escape(None, [element]) == r"**50\%**"
    assert markdown_to_latex(None, [element], False) == r"\textbf{50\%}"
    assert latex_escape(None, "a_b") == r"a\_b"


@pytest.fixture()
def glossary_with_bibliography_item(monkeypatch):
    """
    Glossary with one bibliography item ('Wiegers and Beatty 2013', id
    'bib1') and one glossary item ('loan', id 'loan1'), as the
    GlossaryHandler component builds it in the application.
    """
    from basic.glossary_handler import GlossaryHandler

    monkeypatch.setattr(GlossaryHandler, "object_ids_by_item",
                        {"wiegers and beatty 2013": {"bib1"}, "loan": {"loan1"}})
    monkeypatch.setattr(GlossaryHandler, "items_descriptions", {"bib1": "", "loan1": ""})
    monkeypatch.setattr(GlossaryHandler, "pattern", re.compile(
        r"\b(?<!-)(?:wiegers and beatty 2013|loan)(?!-)\b", re.IGNORECASE))


@pytest.mark.parametrize(
    "markdown, expected",
    [
        ("As in Wiegers and Beatty 2013.", r"As in \cite{bib1}."),
        ("As in [Wiegers and Beatty 2013].", r"As in \cite{bib1}."),
        ("A loan.", r"A \hyperref[loan1]{loan}."),
        ("`Wiegers and Beatty 2013`", r"\texttt{Wiegers and Beatty 2013}"),
    ],
)
def test_markdown_citations(glossary_with_bibliography_item, markdown, expected):
    """
    Glossary links to bibliography items of the document are citations;
    brackets written around them are removed, since \\cite adds them.
    Other glossary items are hyperlinks, and code is not highlighted.
    """
    assert markdown_to_latex_string(markdown, True, ["bib1"]) == expected


def test_markdown_citations_other_documents(glossary_with_bibliography_item):
    """
    Bibliography items that are not in the rendered document (not in the
    citation ids) are hyperlinks, not citations.
    """
    assert markdown_to_latex_string("[Wiegers and Beatty 2013]", True, []) == (
        r"[\hyperref[bib1]{Wiegers and Beatty 2013}]"
    )


def test_xslt_markdown_citation_ids(glossary_with_bibliography_item):
    """
    The XSLT function receives the citation ids as a space-separated string.
    """
    assert markdown_to_latex(None, "Wiegers and Beatty 2013", True, " x bib1 ") == r"\cite{bib1}"


def test_latex_url():
    """
    URLs are hyperlinks whose text is the escaped URL.
    """
    assert (
        latex_url(None, " https://a.org/a_b#c ")
        == r"\href{https://a.org/a_b\#c}{\texttt{https://a.org/a\_b\#c}}"
    )
