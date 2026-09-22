# ==========================================================================
# Plugin: proteus_mcp (ProteusMCP)
# Description: Embedded, profile-agnostic MCP server for the live PROTEUS
#              project. Exposes generic repository-derived inspection and
#              editing operations to AI agents.
# ==========================================================================

import logging

from proteus.application.configuration.config import Config
from proteus_mcp.server import McpServerComponent

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Plugin registration entry point.
# The PROTEUS loader (application/resources/plugins.py) calls register() for
# each plugin. Register a single ProteusComponent that receives the controller
# and hosts the MCP server, unless it has been disabled in proteus.ini
# ([mcp] enabled = False, the default).
# --------------------------------------------------------------------------
def register(
    register_xslt_function,
    register_qwebchannel_class,
    register_proteus_component,
    register_export_strategy,
):
    if not Config().app_settings.mcp_server_enabled:
        log.info(
            "ProteusMCP server disabled (set 'enabled = True' in the [mcp] "
            "section of proteus.ini to enable it)"
        )
        return

    register_proteus_component("proteusMcpServer", McpServerComponent)
