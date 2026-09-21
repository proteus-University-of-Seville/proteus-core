# ==========================================================================
# Plugin: proteus_mcp (ProteusMCP)
# Description: Embedded, profile-agnostic MCP server for the live PROTEUS
#              project. Exposes generic repository-derived inspection and
#              editing operations to AI agents.
# ==========================================================================

from proteus_mcp.server import McpServerComponent


# --------------------------------------------------------------------------
# Plugin registration entry point.
# The PROTEUS loader (application/resources/plugins.py) calls register() for
# each plugin. Register a single ProteusComponent that receives the controller
# and hosts the MCP server.
# --------------------------------------------------------------------------
def register(
    register_xslt_function,
    register_qwebchannel_class,
    register_proteus_component,
    register_export_strategy,
):
    register_proteus_component("proteusMcpServer", McpServerComponent)
