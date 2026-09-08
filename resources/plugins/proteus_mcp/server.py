# ==========================================================================
# File: server.py
# Description: PROTEUS component that hosts the embedded MCP server.
#              Starts FastMCP (streamable-http on loopback) in a daemon thread
#              and exposes generic repository-derived tools.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
import threading

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from fastmcp import FastMCP

# --------------------------------------------------------------------------
# Proteus imports
# --------------------------------------------------------------------------

from proteus.views.components.abstract_component import ProteusComponent

# --------------------------------------------------------------------------
# Plugin imports
# --------------------------------------------------------------------------

from proteus_mcp.bridge import QtBridge
from proteus_mcp.gateway import Gateway
from proteus_mcp import tools as tools_module

# Module configuration
log = logging.getLogger(__name__)

# Server configuration.
# TODO: read host/port/enabled from proteus.ini ([mcp] section), as the prototype did.
HOST = "127.0.0.1"
PORT = 8731


# --------------------------------------------------------------------------
# Function: build_server
# Description: Builds the FastMCP server and generic tools.
# --------------------------------------------------------------------------
def build_server(bridge: QtBridge, controller, state_manager) -> FastMCP:
    """
    Build the FastMCP server, create its Gateway, and register generic tools.
    The bridge marshals each Controller call to the GUI thread.
    """
    mcp = FastMCP("ProteusMCP")
    gateway = Gateway(controller, state_manager)

    tools_module.register_tools(mcp, bridge, gateway)

    return mcp


# --------------------------------------------------------------------------
# Class: McpServerComponent
# Description: ProteusComponent that hosts the embedded MCP server.
# --------------------------------------------------------------------------
class McpServerComponent(ProteusComponent):
    """
    Host the embedded MCP server in the live PROTEUS session.

    Register as a ProteusComponent (receiving the controller from the parent
    MainWindow). Start FastMCP (streamable-http on loopback) in a daemon thread,
    deferred with QTimer.singleShot until Qt's event loop is running.
    """

    def __init__(self, parent=None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        # Create the bridge on the GUI thread (this component's thread affinity).
        self._bridge = QtBridge(self)
        self._mcp = build_server(self._bridge, self._controller, self._state_manager)
        self._thread: threading.Thread | None = None

        # Deferred startup: wait until Qt's event loop is running.
        QTimer.singleShot(0, self._start_server)

        # Best-effort shutdown when the application exits.
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._stop_server)

        log.info("McpServerComponent initialized")

    # ----------------------------------------------------------------------
    # Method: _start_server (runs on the GUI thread, via QTimer)
    # ----------------------------------------------------------------------
    def _start_server(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run, name="ProteusMCP-server", daemon=True
        )
        self._thread.start()
        log.info(
            "ProteusMCP server starting at http://%s:%s/mcp/ (daemon thread)",
            HOST,
            PORT,
        )

    # ----------------------------------------------------------------------
    # Method: _run (runs on the server daemon thread)
    # ----------------------------------------------------------------------
    def _run(self) -> None:
        try:
            self._mcp.run(transport="http", host=HOST, port=PORT)
        except Exception as exc:  # noqa: BLE001
            log.error("ProteusMCP server failed to start: %s", exc)

    # ----------------------------------------------------------------------
    # Method: _stop_server (runs on the GUI thread, via aboutToQuit)
    # ----------------------------------------------------------------------
    def _stop_server(self) -> None:
        # The thread is a daemon: it dies with the process.
        # TODO: clean server shutdown (uvicorn handle / should_exit).
        log.info("Closing ProteusMCP (the application is shutting down)")
