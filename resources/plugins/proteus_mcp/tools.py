# ==========================================================================
# File: tools.py
# Description: Profile-agnostic MCP tools for inspecting and editing PROTEUS.
# ==========================================================================

from fastmcp.exceptions import ToolError

from proteus_mcp import serializers


def _run(bridge, fn):
    """Run a Controller operation on the GUI thread as an MCP tool call."""
    try:
        return bridge.execute(fn)
    except ToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - expose Controller failures to the agent
        raise ToolError(str(exc)) from exc


def register_tools(mcp, bridge, gateway) -> None:
    """Register generic project, schema, and mutation tools."""

    @mcp.tool()
    def get_project_overview() -> str:
        """Return the project document and artifact tree."""

        def _do() -> str:
            project = gateway.get_current_project()
            if project is None:
                raise ToolError("No project is open in PROTEUS.")
            return serializers.overview_md(project, gateway.get_documents(), gateway)

        return _run(bridge, _do)

    @mcp.tool()
    def list_documents() -> str:
        """List the project's top-level documents."""
        return _run(bridge, lambda: serializers.objects_list_md(gateway.get_documents(), "Documents"))

    @mcp.tool()
    def get_object(object_id: str) -> str:
        """Return an artifact's classes, properties, trace schema, and children."""
        return _run(
            bridge,
            lambda: serializers.object_detail_md(gateway.get_element(object_id), gateway),
        )

    @mcp.tool()
    def get_document(document_id: str, max_depth: int | None = None) -> str:
        """Return document content recursively, optionally limited by structural depth."""
        return _run(
            bridge,
            lambda: serializers.document_md(
                gateway.get_element(document_id), gateway, max_depth
            ),
        )

    @mcp.tool()
    def list_objects(classes: list[str] | None = None) -> str:
        """List objects, optionally requiring one of the supplied class tags."""
        return _run(
            bridge,
            lambda: serializers.objects_list_md(gateway.get_objects(classes), "Objects"),
        )

    @mcp.tool()
    def search(query: str) -> str:
        """Search non-trace artifact property values by text."""
        return _run(
            bridge,
            lambda: serializers.objects_list_md(gateway.search(query), f"Search: {query}"),
        )

    @mcp.tool()
    def list_creatable(parent_id: str) -> str:
        """Return every compatible archetype and its property schema for a parent."""
        return _run(
            bridge,
            lambda: serializers.creatable_md(
                gateway.get_creatable_archetypes(parent_id), gateway
            ),
        )

    @mcp.tool()
    def create_artifact(
        parent_id: str, archetype_id: str, values: dict | None = None
    ) -> str:
        """Create a compatible archetype under a parent using its exact archetype id."""
        return _run(
            bridge,
            lambda: serializers.object_detail_md(
                gateway.create_artifact(parent_id, archetype_id, values), gateway
            ),
        )

    @mcp.tool()
    def update_artifact(object_id: str, values: dict) -> str:
        """Update mutable non-code, non-trace properties with typed JSON values."""
        return _run(
            bridge,
            lambda: serializers.object_detail_md(
                gateway.update_fields(object_id, values), gateway
            ),
        )

    @mcp.tool()
    def get_traces(object_id: str) -> str:
        """Return trace properties, raw types, constraints, and current targets."""
        return _run(
            bridge,
            lambda: serializers.traces_md(gateway.get_element(object_id), gateway),
        )

    @mcp.tool()
    def list_trace_targets(object_id: str, trace_property: str) -> str:
        """List targets eligible for a named trace property."""

        def _do() -> str:
            element = gateway.get_element(object_id)
            return serializers.trace_targets_md(
                element,
                trace_property,
                gateway.get_trace_targets(object_id, trace_property),
                gateway,
            )

        return _run(bridge, _do)

    @mcp.tool()
    def add_trace(source_id: str, trace_property: str, target_id: str) -> str:
        """Add a target to a named trace property after schema validation."""

        def _do() -> str:
            gateway.add_trace(source_id, trace_property, target_id)
            return (
                f"Added {gateway.ref_by_id(target_id)} to `{trace_property}` on "
                f"{gateway.ref_by_id(source_id)}."
            )

        return _run(bridge, _do)

    @mcp.tool()
    def remove_trace(source_id: str, trace_property: str, target_id: str) -> str:
        """Remove a target from a named trace property."""

        def _do() -> str:
            gateway.remove_trace(source_id, trace_property, target_id)
            return (
                f"Removed {gateway.ref_by_id(target_id)} from `{trace_property}` on "
                f"{gateway.ref_by_id(source_id)}."
            )

        return _run(bridge, _do)

    @mcp.tool()
    def get_backlinks(object_id: str) -> str:
        """Return artifacts whose traces point to this artifact."""

        def _do() -> str:
            element = gateway.get_element(object_id)
            return serializers.backlinks_md(
                element, gateway.get_backlinks(object_id), gateway
            )

        return _run(bridge, _do)

    @mcp.tool()
    def delete_artifact(object_id: str) -> str:
        """Delete an artifact."""

        def _do() -> str:
            reference = gateway.ref_by_id(object_id)
            gateway.delete_object(object_id)
            return f"Deleted {reference}."

        return _run(bridge, _do)

    @mcp.tool()
    def move_artifact(
        object_id: str, new_parent_id: str, position: int | None = None
    ) -> str:
        """Move an artifact to a compatible parent and optional position."""

        def _do() -> str:
            gateway.move_object(object_id, new_parent_id, position)
            return f"Moved {gateway.ref_by_id(object_id)} to {gateway.ref_by_id(new_parent_id)}."

        return _run(bridge, _do)

    @mcp.tool()
    def focus_object(object_id: str) -> str:
        """Focus the PROTEUS GUI on an artifact."""
        def _do() -> str:
            gateway.focus_object(object_id)
            return f"Focused {gateway.ref_by_id(object_id)} in the PROTEUS GUI."

        return _run(bridge, _do)
