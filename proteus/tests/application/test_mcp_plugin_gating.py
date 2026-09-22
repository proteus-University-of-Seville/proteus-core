# ==========================================================================
# File: test_mcp_plugin_gating.py
# Description: pytest file checking that the embedded proteus_mcp plugin
#              only registers its ProteusComponent (and therefore only
#              starts the MCP server) when explicitly enabled in
#              proteus.ini ([mcp] enabled = True). Disabled is the default.
# Date: 22/09/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.configuration.config import Config

PLUGIN_DIR = Path("resources/plugins").resolve()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _fresh_register():
    """
    Import (or re-import) the proteus_mcp plugin package and return its
    register() function. Re-importing is necessary because register() reads
    Config() at call time and modules are cached by Python after the first
    import within the test session.
    """
    sys.path.insert(0, str(PLUGIN_DIR))
    for mod_name in list(sys.modules):
        if mod_name == "proteus_mcp" or mod_name.startswith("proteus_mcp."):
            del sys.modules[mod_name]
    import proteus_mcp  # noqa: E402

    return proteus_mcp.register


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


def test_mcp_plugin_not_registered_when_disabled(app_settings_test_config):
    """
    Check that the MCP server component is not registered (and therefore
    never instantiated/started) when mcp_server_enabled is False, which is
    the default.
    """
    Config().app_settings.mcp_server_enabled = False
    register = _fresh_register()

    registered = {}
    register(
        register_xslt_function=lambda *a, **k: None,
        register_qwebchannel_class=lambda *a, **k: None,
        register_proteus_component=lambda name, cls: registered.__setitem__(name, cls),
        register_export_strategy=lambda *a, **k: None,
    )

    assert registered == {}, f"Expected no component registered, got {registered}"


def test_mcp_plugin_registered_when_enabled(app_settings_test_config):
    """
    Check that the MCP server component is registered when mcp_server_enabled
    is explicitly set to True.
    """
    Config().app_settings.mcp_server_enabled = True
    register = _fresh_register()

    registered = {}
    register(
        register_xslt_function=lambda *a, **k: None,
        register_qwebchannel_class=lambda *a, **k: None,
        register_proteus_component=lambda name, cls: registered.__setitem__(name, cls),
        register_export_strategy=lambda *a, **k: None,
    )

    assert "proteusMcpServer" in registered, f"Expected proteusMcpServer registered, got {registered}"
