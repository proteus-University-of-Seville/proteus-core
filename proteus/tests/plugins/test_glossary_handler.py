# ==========================================================================
# File: test_glossary_handler.py
# Description: tests of the highlighting of glossary items, in particular of
#              the items whose capitalization is significant (acronyms)
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import re
import sys
from pathlib import Path
from types import SimpleNamespace

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

PLUGIN_DIR = Path("resources/plugins").resolve()
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from basic.glossary_handler import GlossaryHandler, is_case_significant  # noqa: E402


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def glossary_item(object_id, name, synonyms="", plural_form=""):
    """
    Object with the properties of a glossary item that the handler reads.
    """
    properties = {
        ":Proteus-name": SimpleNamespace(value=name),
        "synonyms": SimpleNamespace(value=synonyms),
        "plural-form": SimpleNamespace(value=plural_form),
        "description": SimpleNamespace(value=f"Description of {name}"),
    }
    return SimpleNamespace(id=object_id, get_property=properties.get)


@pytest.fixture()
def glossary(monkeypatch):
    """
    Empty glossary. Returns a function that adds glossary items to it and
    updates the pattern, as the handler does when a project is opened.
    """
    monkeypatch.setattr(GlossaryHandler, "items_descriptions", dict())
    monkeypatch.setattr(GlossaryHandler, "object_ids_by_item", dict())
    monkeypatch.setattr(GlossaryHandler, "object_ids_by_exact_item", dict())
    monkeypatch.setattr(GlossaryHandler, "pattern", None)

    handler = GlossaryHandler.__new__(GlossaryHandler)

    def add(*items):
        for item in items:
            handler._add_glossary_item(item)
        handler._setup_pattern()
        return handler

    return add


def linked(text, object_id):
    """
    Number of links to the given glossary item in the highlighted text.
    """
    html = GlossaryHandler.highlight_glossary_items(None, text)
    return len(re.findall(rf'href="#{object_id}"', html))


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "term, expected",
    [
        ("IT", True),
        ("IoT", True),
        ("SaaS", True),
        ("eID", True),
        ("KPIs", True),
        ("C", True),
        ("IT department", True),
        ("it", False),
        ("a", False),
        ("Member", False),
        ("Annual fee", False),
        ("Municipal Sports Board", False),
        ("Information Technology", False),
    ],
)
def test_is_case_significant(term, expected):
    assert is_case_significant(term) == expected


def test_acronym_is_found_only_with_its_capitalization(glossary):
    glossary(glossary_item("it1", "IT"))

    assert linked("The IT department", "it1") == 1
    assert linked("It works, but it is slow", "it1") == 0


def test_terms_with_initial_capitals_ignore_case(glossary):
    glossary(glossary_item("m1", "Member"), glossary_item("f1", "Annual fee"))

    assert linked("A member pays the annual fee. Member.", "m1") == 2
    assert linked("The ANNUAL FEE and the Annual Fee", "f1") == 2


@pytest.mark.parametrize("term, found, not_found", [
    ("IoT", "IoT devices", "iot devices"),
    ("SaaS", "a SaaS product", "a saas product"),
    ("C", "written in C.", "plan c."),
])
def test_other_case_significant_terms(glossary, term, found, not_found):
    glossary(glossary_item("t1", term))

    assert linked(found, "t1") == 1
    assert linked(not_found, "t1") == 0


def test_name_synonyms_and_plural_forms_are_considered_separately(glossary):
    glossary(glossary_item("it1", "IT", synonyms="Information Technology"),
             glossary_item("k1", "KPI", plural_form="KPIs"))

    assert linked("information technology and IT", "it1") == 2
    assert linked("it is", "it1") == 0
    assert linked("one KPI, two KPIs", "k1") == 2
    assert linked("two kpis", "k1") == 0


def test_longest_item_wins_whatever_its_capitalization(glossary):
    glossary(glossary_item("it1", "IT"), glossary_item("g1", "it governance"))

    assert linked("IT governance", "g1") == 1
    assert linked("IT governance", "it1") == 0
    assert linked("IT budget", "it1") == 1


def test_acronym_and_word_with_the_same_letters(glossary):
    glossary(glossary_item("it1", "IT"), glossary_item("w1", "it"))

    assert linked("IT", "it1") == 1
    assert linked("it", "w1") == 1
    assert linked("it", "it1") == 0


def test_items_in_code_are_not_highlighted(glossary):
    glossary(glossary_item("it1", "IT"))

    assert linked("<code>IT</code> and IT", "it1") == 1


def test_deleted_case_significant_items_are_not_highlighted(glossary):
    handler = glossary(glossary_item("it1", "IT"))

    handler._delete_glossary_item("it1")
    handler._setup_pattern()

    assert GlossaryHandler.object_ids_by_exact_item == {}
    assert linked("IT", "it1") == 0
