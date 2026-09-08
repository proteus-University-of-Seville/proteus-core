# ==========================================================================
# File: serializers.py
# Description: Generic Markdown serializers for PROTEUS artifacts and schemas.
# ==========================================================================

import json
from typing import Iterable

from proteus.application.resources.translator import translate
from proteus.model import PROTEUS_CODE, PROTEUS_NAME
from proteus.model.abstract_object import ProteusState
from proteus.model.properties import CodeProperty, Property, TraceProperty


def _label(key: str, fallback: str) -> str:
    return translate(key, alternative_text=fallback)


def class_labels(classes: Iterable[str]) -> list[str]:
    """Return localized labels for class tags without assigning a primary class."""
    return [_label(f"archetype.class.{class_name}", class_name) for class_name in classes]


def property_label(name: str) -> str:
    """Return the profile-localized label for a property name."""
    return _label(f"archetype.prop_name.{name}", name)


def element_name(element) -> str:
    """Return an element name, falling back to its id."""
    prop = element.get_property(PROTEUS_NAME)
    return str(prop.value) if prop is not None and prop.value else str(element.id)


def ref(element) -> str:
    """Return a readable element reference."""
    return f"{element_name(element)} (`{element.id}`)"


def property_schema(prop: Property, gateway) -> dict:
    """Serialize a property definition and value using generic metadata."""
    schema = {
        "name": prop.name,
        "label": property_label(prop.name),
        "type": prop.element_tagname,
        "category": prop.category,
        "required": prop.required,
        "immutable": prop.inmutable,
        "tooltip": prop.tooltip,
        "value": gateway.property_value(prop),
    }
    if hasattr(prop, "choices"):
        schema["choices"] = prop.get_choices_as_list()
    if hasattr(prop, "units"):
        schema["units"] = prop.units
    if isinstance(prop, TraceProperty):
        schema.update(
            {
                "trace_type": prop.traceType,
                "accepted_target_classes": prop.acceptedTargets,
                "excluded_target_classes": prop.excludedTargets,
                "max_targets": prop.maxTargetsNumber,
            }
        )
    return schema


def archetype_schema(archetype, gateway) -> dict:
    """Serialize an archetype as a generic creation schema."""
    properties = [property_schema(prop, gateway) for prop in archetype.properties.values()]
    return {
        "archetype_id": archetype.id,
        "classes": list(getattr(archetype, "classes", []) or []),
        "class_labels": class_labels(getattr(archetype, "classes", []) or []),
        "accepted_parents": list(getattr(archetype, "acceptedParents", []) or []),
        "accepted_children": list(getattr(archetype, "acceptedChildren", []) or []),
        "properties": properties,
    }


def artifact_schema(element, gateway) -> dict:
    """Serialize an existing artifact without profile-specific interpretations."""
    properties = [property_schema(prop, gateway) for prop in element.properties.values()]
    return {
        "id": element.id,
        "name": element_name(element),
        "classes": list(getattr(element, "classes", []) or []),
        "class_labels": class_labels(getattr(element, "classes", []) or []),
        "properties": properties,
    }


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def summary_line(element, indent: int = 0) -> str:
    """Return a structural summary line without assuming a primary class."""
    classes = list(getattr(element, "classes", []) or [])
    type_info = ", ".join(classes) if classes else "project"
    code = element.get_property(PROTEUS_CODE)
    code_value = gateway_value(code) if isinstance(code, CodeProperty) else None
    suffix = f" [{code_value}]" if code_value else ""
    return f"{'  ' * indent}- {ref(element)} [{type_info}]{suffix}"


def gateway_value(prop: Property):
    """Return a display value for code properties without a gateway instance."""
    return prop.value.to_string() if prop.value is not None else ""


def _tree_lines(element, indent: int, lines: list[str]) -> None:
    lines.append(summary_line(element, indent))
    for child in getattr(element, "children", []):
        if child.state != ProteusState.DEAD:
            _tree_lines(child, indent + 1, lines)


def overview_md(project, documents: list, gateway) -> str:
    """Return the project document and object tree."""
    lines = [f"# Project: {ref(project)}"]
    for document in documents:
        if document.state != ProteusState.DEAD:
            _tree_lines(document, 0, lines)
    return "\n".join(lines)


def object_detail_md(element, gateway, include_children: bool = True) -> str:
    """Return an artifact's generic schema and optional direct children."""
    blocks = [f"# {ref(element)}", "```json\n" + _json(artifact_schema(element, gateway)) + "\n```"]
    if include_children:
        children = [
            summary_line(child)
            for child in getattr(element, "children", [])
            if child.state != ProteusState.DEAD
        ]
        if children:
            blocks.append("## Children\n" + "\n".join(children))
    return "\n\n".join(blocks)


def document_md(document, gateway, max_depth: int | None = None) -> str:
    """Return a document recursively, optionally limited by structural depth."""
    blocks = []

    def append(element, depth: int) -> None:
        blocks.append(object_detail_md(element, gateway, include_children=False))
        if max_depth is None or depth < max_depth:
            for child in getattr(element, "children", []):
                if child.state != ProteusState.DEAD:
                    append(child, depth + 1)

    append(document, 0)
    return "\n\n---\n\n".join(blocks)


def objects_list_md(objects: list, title: str) -> str:
    """Return a list of live objects."""
    lines = [summary_line(element) for element in objects if element.state != ProteusState.DEAD]
    return f"# {title}\n\n" + ("\n".join(lines) if lines else "_No results._")


def creatable_md(archetypes: list, gateway) -> str:
    """Return compatible archetypes and their exact creation schemas."""
    schemas = [archetype_schema(archetype, gateway) for archetype in archetypes]
    return "# Creatable archetypes\n\n```json\n" + _json(schemas) + "\n```"


def traces_md(element, gateway) -> str:
    """Return outgoing trace values with raw trace schema identifiers."""
    traces = [
        property_schema(trace, gateway)
        for trace in element.properties.values()
        if isinstance(trace, TraceProperty)
    ]
    return "# Trace schema\n\n```json\n" + _json(traces) + "\n```"


def trace_targets_md(element, trace_property: str, targets: list, gateway) -> str:
    """Return target candidates for a named trace property."""
    return (
        f"# Eligible targets for `{trace_property}` on {ref(element)}\n\n"
        + objects_list_md(targets, "Targets").removeprefix("# Targets\n\n")
    )


def backlinks_md(element, pairs: set[tuple[str, str]], gateway) -> str:
    """Return reverse trace links using raw trace types."""
    lines = [f"- {gateway.ref_by_id(source_id)} [{trace_type}]" for source_id, trace_type in sorted(pairs)]
    return f"# Backlinks to {ref(element)}\n\n" + ("\n".join(lines) if lines else "_No backlinks._")
