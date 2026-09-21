# ==========================================================================
# File: gateway.py
# Description: Profile-agnostic operations over the PROTEUS Controller.
# ==========================================================================

from typing import Any

from proteus.model import PROTEUS_NAME, ProteusID
from proteus.model.object import Object
from proteus.model.project import Project
from proteus.model.properties import CodeProperty, Property, TraceProperty, UnitProperty
from proteus.model.properties.unit_property import Measurement


class Gateway:
    """Expose generic project, archetype, property, and trace operations."""

    def __init__(self, controller, state_manager) -> None:
        self._controller = controller
        self._state_manager = state_manager

    def get_element(self, element_id: ProteusID):
        """Return an element by id."""
        return self._controller.get_element(element_id)

    def get_current_project(self) -> Project | None:
        """Return the open project, if any."""
        return self._controller.get_current_project()

    def get_documents(self) -> list[Object]:
        """Return the project's top-level documents."""
        return self._controller.get_project_structure()

    def get_objects(self, classes: list[str] | None = None) -> list[Object]:
        """Return project objects, optionally filtered by class tags."""
        return self._controller.get_objects(classes or [])

    def get_backlinks(self, element_id: ProteusID) -> set[tuple[ProteusID, str]]:
        """Return source ids and trace types pointing to an element."""
        return self._controller.get_objects_pointing_to(element_id)

    def search(self, query: str) -> list[Object]:
        """Find objects whose non-trace values contain the query."""
        needle = (query or "").strip().lower()
        if not needle:
            return []
        return [obj for obj in self.get_objects() if self._object_matches(obj, needle)]

    def _object_matches(self, element: Object, needle: str) -> bool:
        for prop in element.properties.values():
            if isinstance(prop, TraceProperty):
                continue
            if needle in str(self.property_value(prop)).lower():
                return True
        return False

    def get_creatable_archetypes(self, parent_id: ProteusID) -> list[Object]:
        """Return every repository archetype compatible with the parent."""
        return self._controller.get_creatable_archetypes(parent_id)

    def create_artifact(
        self, parent_id: ProteusID, archetype_id: ProteusID, values: dict | None = None
    ) -> Object:
        """Create a compatible archetype and optionally set mutable properties."""
        parent = self.get_element(parent_id)
        archetype = next(
            (
                item
                for item in self.get_creatable_archetypes(parent_id)
                if item.id == archetype_id
            ),
            None,
        )
        if archetype is None:
            raise ValueError(
                f"Archetype '{archetype_id}' cannot be created below '{parent_id}'."
            )

        if isinstance(parent, Project):
            new_id = self._controller.create_document(archetype.id)
        else:
            new_id = self._controller.create_object(archetype.id, parent_id)

        if values:
            self.update_fields(new_id, values)
        return self.get_element(new_id)

    def update_fields(self, element_id: ProteusID, values: dict) -> Object:
        """Update mutable non-code, non-trace properties from JSON-compatible values."""
        element = self.get_element(element_id)
        properties = self.build_field_properties(element, values)
        if properties:
            self._controller.update_properties(element_id, properties)
        return self.get_element(element_id)

    def build_field_properties(self, element: Object, values: dict) -> list[Property]:
        """Clone mutable properties with values converted for their concrete type."""
        properties = []
        for name, value in values.items():
            prop = element.get_property(name)
            if prop is None:
                raise ValueError(f"Property '{name}' does not exist on '{element.id}'.")
            if isinstance(prop, TraceProperty):
                raise ValueError(f"Property '{name}' is a trace; use add_trace/remove_trace.")
            if isinstance(prop, CodeProperty):
                raise ValueError(f"Property '{name}' is generated code and cannot be updated.")
            if prop.inmutable:
                raise ValueError(f"Property '{name}' is immutable.")
            properties.append(prop.clone(self._property_input_value(prop, value)))
        return properties

    def _property_input_value(self, prop: Property, value: Any) -> Any:
        if isinstance(prop, UnitProperty):
            if not isinstance(value, dict) or set(value) != {"value", "unit"}:
                raise ValueError(
                    f"Unit property '{prop.name}' requires {{'value': number, 'unit': string}}."
                )
            return Measurement(value=value["value"], unit=value["unit"])
        return value

    def get_trace(self, element_id: ProteusID, trace_property: str) -> TraceProperty:
        """Return a named trace property from an element."""
        prop = self.get_element(element_id).get_property(trace_property)
        if not isinstance(prop, TraceProperty):
            raise ValueError(f"Property '{trace_property}' is not a trace on '{element_id}'.")
        return prop

    def get_trace_targets(
        self, element_id: ProteusID, trace_property: str
    ) -> list[Object]:
        """Return targets permitted by the trace schema."""
        return self._controller.get_trace_targets(element_id, trace_property)

    def add_trace(
        self, source_id: ProteusID, trace_property: str, target_id: ProteusID
    ) -> None:
        """Add a target after validating it against the trace schema."""
        trace = self.get_trace(source_id, trace_property)
        if target_id in trace.value:
            return
        if trace.maxTargetsNumber != -1 and len(trace.value) >= trace.maxTargetsNumber:
            raise ValueError(f"Trace property '{trace_property}' has reached its target limit.")
        if target_id not in {target.id for target in self.get_trace_targets(source_id, trace_property)}:
            raise ValueError(
                f"Target '{target_id}' is not allowed by trace property '{trace_property}'."
            )
        self._controller.update_properties(
            source_id, [trace.clone(list(trace.value) + [target_id])]
        )

    def remove_trace(
        self, source_id: ProteusID, trace_property: str, target_id: ProteusID
    ) -> None:
        """Remove a target from a trace property."""
        trace = self.get_trace(source_id, trace_property)
        targets = [target for target in trace.value if target != target_id]
        if targets != list(trace.value):
            self._controller.update_properties(source_id, [trace.clone(targets)])

    def delete_object(self, object_id: ProteusID) -> None:
        """Delete an object."""
        self._controller.delete_object(object_id)

    def move_object(
        self, object_id: ProteusID, new_parent_id: ProteusID, position: int | None = None
    ) -> None:
        """Move an object to a new parent and optional position."""
        self._controller.change_object_position(object_id, new_parent_id, position)

    def focus_object(self, object_id: ProteusID) -> None:
        """Move the GUI view to an object and its document."""
        element = self.get_element(object_id)
        document = element.get_document()
        self._state_manager.set_current_document(document.id)
        self._state_manager.set_current_object(object_id, document.id)

    @staticmethod
    def property_value(prop: Property) -> Any:
        """Return a property value in a JSON-compatible representation."""
        if isinstance(prop, CodeProperty):
            return prop.value.to_string() if prop.value is not None else ""
        value = prop.value
        if isinstance(value, Measurement):
            return {"value": value.value, "unit": value.unit}
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    def name_of(self, element_id: ProteusID) -> str:
        """Return a readable element name, falling back to its id."""
        try:
            prop = self.get_element(element_id).get_property(PROTEUS_NAME)
            if prop is not None and prop.value:
                return str(prop.value)
        except Exception:  # noqa: BLE001 - references may be stale
            pass
        return str(element_id)

    def ref_by_id(self, element_id: ProteusID) -> str:
        """Return a readable element reference."""
        return f"{self.name_of(element_id)} (`{element_id}`)"
