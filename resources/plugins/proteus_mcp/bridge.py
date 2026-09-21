# ==========================================================================
# File: bridge.py
# Description: QtBridge. Safely (thread-safe) executes calls on Qt's main
#              thread from the MCP server thread.
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
import threading

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

# Module configuration
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Class: QtBridge
# Description: Cross-thread bridge between the MCP server and Qt's GUI thread.
# --------------------------------------------------------------------------
class QtBridge(QObject):
    """
    Bridge between the MCP server thread and Qt's main thread.

    The PROTEUS Controller assumes the GUI thread (emits PyQt signals, uses
    QUndoStack). MCP tools run on a separate thread, so every call to the
    Controller runs through `execute`, which queues it on the GUI thread and
    blocks until it gets the result (equivalent to
    QMetaObject.invokeMethod con QueuedConnection).

    It must be instantiated on the GUI thread (the QObject's thread affinity) so
    the `_invoke` signal, emitted from the server thread, is queued to the GUI
    thread.
    """

    # Signal carrying a "call" (dict with fn/result/error/event).
    _invoke = pyqtSignal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # AutoConnection: when emitted from another thread, Qt queues it and
        # executes the slot on this object's affinity thread (the GUI).
        self._invoke.connect(self._on_invoke)

    # ----------------------------------------------------------------------
    # Method: _on_invoke (runs on the GUI thread)
    # ----------------------------------------------------------------------
    @pyqtSlot(object)
    def _on_invoke(self, call: dict) -> None:
        try:
            call["result"] = call["fn"]()
        except BaseException as exc:  # forwarded to the calling thread
            call["error"] = exc
        finally:
            call["event"].set()

    # ----------------------------------------------------------------------
    # Method: execute (runs on the MCP server thread)
    # ----------------------------------------------------------------------
    def execute(self, fn):
        """
        Execute `fn` on the GUI thread and return its result. Block the calling
        thread until the GUI thread finishes. If `fn` raises, re-raise it here.
        """
        # Execute directly when already on the GUI thread (avoids deadlock).
        if QThread.currentThread() is self.thread():
            return fn()

        call = {
            "fn": fn,
            "result": None,
            "error": None,
            "event": threading.Event(),
        }
        self._invoke.emit(call)
        call["event"].wait()

        if call["error"] is not None:
            raise call["error"]
        return call["result"]
