# ==========================================================================
# File: test_mcp_client_config.py
# Description: pytest file for the generation of the .mcp.json file
# Date: 22/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import json
from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.configuration.mcp_client_config import (
    MCP_CLIENT_CONFIG_FILE,
    mcp_server_url,
    write_mcp_client_config,
)

# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "host, port, expected_url",
    [
        ("127.0.0.1", 8731, "http://127.0.0.1:8731/mcp/"),
        ("localhost", 9000, "http://localhost:9000/mcp/"),
        ("0.0.0.0", 8731, "http://127.0.0.1:8731/mcp/"),
        ("::", 8731, "http://127.0.0.1:8731/mcp/"),
        ("::1", 8731, "http://[::1]:8731/mcp/"),
        (" 192.168.1.10 ", 8731, "http://192.168.1.10:8731/mcp/"),
    ],
)
def test_mcp_server_url(host: str, port: int, expected_url: str):
    """
    Check the URL a client uses to connect to the MCP server.
    """
    assert (
        mcp_server_url(host, port) == expected_url
    ), f"Expected URL '{expected_url}', but got '{mcp_server_url(host, port)}'"


def test_write_mcp_client_config_new_file(tmp_path: Path):
    """
    Check that the .mcp.json file is created when it does not exist.
    """
    config_path = write_mcp_client_config(tmp_path, "127.0.0.1", 8731)

    assert config_path == tmp_path / MCP_CLIENT_CONFIG_FILE
    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "mcpServers": {
            "proteus": {"type": "http", "url": "http://127.0.0.1:8731/mcp/"}
        }
    }


def test_write_mcp_client_config_merge(tmp_path: Path):
    """
    Check that other servers and keys of an existing .mcp.json file are kept
    and that an existing proteus entry is updated.
    """
    config_path = tmp_path / MCP_CLIENT_CONFIG_FILE
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "other": {"command": "other-server"},
                    "proteus": {"type": "http", "url": "http://127.0.0.1:1/mcp/"},
                },
                "otherKey": True,
            }
        ),
        encoding="utf-8",
    )

    write_mcp_client_config(tmp_path, "localhost", 9000)

    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "mcpServers": {
            "other": {"command": "other-server"},
            "proteus": {"type": "http", "url": "http://localhost:9000/mcp/"},
        },
        "otherKey": True,
    }


@pytest.mark.parametrize(
    "content",
    [
        "{ not json",
        "[]",
        '{"mcpServers": []}',
    ],
)
def test_write_mcp_client_config_invalid_file(tmp_path: Path, content: str):
    """
    Check that an invalid .mcp.json file raises ValueError and is not
    modified.
    """
    config_path = tmp_path / MCP_CLIENT_CONFIG_FILE
    config_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        write_mcp_client_config(tmp_path, "127.0.0.1", 8731)

    assert (
        config_path.read_text(encoding="utf-8") == content
    ), "Invalid .mcp.json file should not be modified"


def test_write_mcp_client_config_empty_file(tmp_path: Path):
    """
    Check that an empty .mcp.json file is filled with the proteus entry.
    """
    config_path = tmp_path / MCP_CLIENT_CONFIG_FILE
    config_path.write_text("", encoding="utf-8")

    write_mcp_client_config(tmp_path, "127.0.0.1", 8731)

    assert "proteus" in json.loads(config_path.read_text(encoding="utf-8"))[
        "mcpServers"
    ]
