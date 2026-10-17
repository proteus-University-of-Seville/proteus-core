# ==========================================================================
# File: test_traceability_matrix_helper.py
# Description: tests of the order of the objects of a traceability matrix
# ==========================================================================

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PLUGIN_DIR = Path("resources/plugins").resolve()
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from basic.traceability_matrix_helper import TraceabilityMatrixHelper, class_group  # noqa: E402


def fake_object(object_id, classes, code):
    properties = {
        ":Proteus-code": SimpleNamespace(value=SimpleNamespace(to_string=lambda: code)),
    }
    return SimpleNamespace(id=object_id, classes=classes, get_property=properties.get)


@pytest.mark.parametrize(
    "object_classes, class_list, expected",
    [
        (["use-case"], ["general-requirement", "use-case"], 1),
        (["software-requirement", "general-requirement"], ["general-requirement", "use-case"], 0),
        (["use-case"], ["use-case", "general-requirement"], 0),
        (["paragraph"], ["general-requirement", "use-case"], 2),
        (["use-case"], [], 0),
    ],
)
def test_class_group(object_classes, class_list, expected):
    assert class_group(object_classes, class_list) == expected


def objects_of_the_matrix(classes):
    helper = TraceabilityMatrixHelper.__new__(TraceabilityMatrixHelper)
    project_objects = [
        fake_object("u2", ["use-case"], "CU-002"),
        fake_object("g2", ["general-requirement"], "RQG-002"),
        fake_object("u1", ["use-case"], "CU-001"),
        fake_object("g1", ["general-requirement"], "RQG-001"),
    ]
    helper._controller = SimpleNamespace(
        get_objects=lambda class_list: [
            obj for obj in project_objects if set(class_list) & set(obj.classes)
        ]
    )
    nodes = helper.get_objects_from_classes(None, [classes])
    return [node.get("id") for node in nodes]


def test_objects_are_grouped_by_class_in_the_order_of_the_classes():
    assert objects_of_the_matrix("general-requirement use-case") == ["g1", "g2", "u1", "u2"]
    assert objects_of_the_matrix("use-case general-requirement") == ["u1", "u2", "g1", "g2"]


def test_objects_of_one_class_are_sorted_by_label():
    assert objects_of_the_matrix("use-case") == ["u1", "u2"]
