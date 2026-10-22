# ==========================================================================
# File: mcp_client_config.py
# Description: Generation of the .mcp.json file that lets MCP clients such
#              as Claude Code connect to the embedded PROTEUS MCP server
# Date: 21/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import json
import logging
from pathlib import Path

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

MCP_CLIENT_CONFIG_FILE: str = ".mcp.json"
MCP_SERVERS_KEY: str = "mcpServers"
PROTEUS_MCP_SERVER_NAME: str = "proteus"

# Hosts the server listens on that cannot be used by a client to connect.
# The client connects through the loopback interface instead.
WILDCARD_HOSTS: list[str] = ["", "0.0.0.0", "::"]
LOOPBACK_HOST: str = "127.0.0.1"

# logging configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Function: mcp_server_url
# Description: Return the URL a client uses to connect to the MCP server
# Date: 21/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
def mcp_server_url(host: str, port: int) -> str:
    """
    Return the URL a client uses to connect to the MCP server listening on
    the given host and port. Wildcard hosts are replaced by the loopback
    address and IPv6 addresses are enclosed in brackets.
    """
    host = host.strip()
    if host in WILDCARD_HOSTS:
        host = LOOPBACK_HOST
    elif ":" in host:
        host = f"[{host}]"

    return f"http://{host}:{port}/mcp/"


# --------------------------------------------------------------------------
# Function: write_mcp_client_config
# Description: Create or update the .mcp.json file in a directory
# Date: 21/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------
def write_mcp_client_config(directory: Path, host: str, port: int) -> Path:
    """
    Create or update the .mcp.json file in the given directory so that it
    contains the PROTEUS MCP server entry. Other servers and keys of an
    existing file are kept.

    :param directory: Directory where the .mcp.json file is written.
    :param host: Host the MCP server listens on.
    :param port: Port the MCP server listens on.
    :return: Path of the written file.
    :raises ValueError: If the existing file is not a valid .mcp.json file.
        In that case it is not modified.
    :raises OSError: If the file cannot be read or written.
    """
    config_path: Path = directory / MCP_CLIENT_CONFIG_FILE

    # Load the existing configuration, never overwrite an invalid one
    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError as e:
            raise ValueError(f"'{config_path}' is not a valid JSON file: {e}") from e

        if not isinstance(config, dict) or not isinstance(
            config.get(MCP_SERVERS_KEY, {}), dict
        ):
            raise ValueError(f"'{config_path}' is not a valid MCP configuration file")

    config.setdefault(MCP_SERVERS_KEY, {})[PROTEUS_MCP_SERVER_NAME] = {
        "type": "http",
        "url": mcp_server_url(host, port),
    }

    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    log.info(f"MCP client configuration written to '{config_path}'.")

    return config_path
