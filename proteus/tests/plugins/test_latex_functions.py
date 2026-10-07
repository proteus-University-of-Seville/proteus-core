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

    assert result.startswith("\\begin{proteusmdtable}{XX}")
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


def test_latex_url():
    """
    URLs are hyperlinks whose text is the escaped URL.
    """
    assert (
        latex_url(None, " https://a.org/a_b#c ")
        == r"\href{https://a.org/a_b\#c}{\texttt{https://a.org/a\_b\#c}}"
    )
