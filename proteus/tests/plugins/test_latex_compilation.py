# ==========================================================================
# File: test_latex_compilation.py
# Description: pytest file for the number of LaTeX passes and the
#              cancellation of the task that writes the LaTeX sources
#              (resources/plugins/basic/export/export_latex.py)
# Date: 08/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import io
import sys
import threading
from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

PLUGIN_DIR = Path("resources/plugins").resolve()
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from basic.export import export_latex  # noqa: E402
from basic.export.export_latex import (  # noqa: E402
    LATEX_MAX_PASSES,
    LATEX_MIN_PASSES,
    LaTeXSourcesTask,
    latex_auxiliary_digest,
    latex_rerun_needed,
)

PNG_DATA = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
URL_1 = "https://example.org/one.png"
URL_2 = "https://example.org/two.png"


# --------------------------------------------------------------------------
# Number of passes
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "passes, same_digest, log_text, expected",
    [
        # Always at least LATEX_MIN_PASSES, even if nothing changed
        (1, True, "", True),
        # Stable auxiliary files and no warnings: done
        (LATEX_MIN_PASSES, True, "", False),
        # Auxiliary files changed in the last pass (e.g. page numbers in the toc)
        (LATEX_MIN_PASSES, False, "", True),
        # Warnings asking for another pass
        (LATEX_MIN_PASSES, True, "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.", True),
        (LATEX_MIN_PASSES, True, "Package rerunfilecheck Warning: File `main.out' has changed.\n(rerunfilecheck) Rerun to get outlines right", True),
        # Never more than LATEX_MAX_PASSES
        (LATEX_MAX_PASSES, False, "Rerun to get cross-references right.", False),
    ],
)
def test_latex_rerun_needed(passes, same_digest, log_text, expected):
    digest = "a"
    previous_digest = "a" if same_digest else "b"

    assert latex_rerun_needed(passes, previous_digest, digest, log_text) == expected


def test_latex_auxiliary_digest(tmp_path: Path):
    """
    The digest changes when an auxiliary file changes or appears, and not
    when other files (e.g. the log or the PDF) change.
    """
    empty = latex_auxiliary_digest(tmp_path)

    (tmp_path / "main.aux").write_text("\\relax\n")
    with_aux = latex_auxiliary_digest(tmp_path)
    assert with_aux != empty

    (tmp_path / "main.log").write_text("log")
    (tmp_path / "main.pdf").write_bytes(b"%PDF")
    assert latex_auxiliary_digest(tmp_path) == with_aux

    (tmp_path / "main.toc").write_text("\\contentsline {section}{1}{3}\n")
    with_toc = latex_auxiliary_digest(tmp_path)
    assert with_toc != with_aux

    (tmp_path / "main.toc").write_text("\\contentsline {section}{1}{5}\n")
    assert latex_auxiliary_digest(tmp_path) != with_toc


# --------------------------------------------------------------------------
# Cancellation of LaTeXSourcesTask
# --------------------------------------------------------------------------


def test_latex_sources_task_cancelled(monkeypatch, tmp_path: Path, qtbot):
    """
    A task cancelled while downloading stops before the next download,
    removes its folder and does not emit its finished signal.
    """
    downloading = threading.Event()
    release = threading.Event()
    requested = []

    def urlopen(request, timeout=None):
        requested.append(request.full_url)
        downloading.set()
        release.wait(10)
        return io.BytesIO(PNG_DATA)

    monkeypatch.setattr(export_latex.urllib.request, "urlopen", urlopen)

    folder = tmp_path / "sources"
    folder.mkdir()
    (folder / "resources.sty").write_text("% copied by prepare_latex_sources")
    tex = f"\\ProteusRemoteImage{{0.5}}{{{URL_1}}} \\ProteusRemoteImage{{0.5}}{{{URL_2}}}"

    task = LaTeXSourcesTask(tex, folder)
    finished = []
    task.signals.finished.connect(lambda *args: finished.append(args))
    task.start()

    assert downloading.wait(10), "The first download must start"
    assert task.cancel(), "A running task must accept the cancellation"
    release.set()

    qtbot.waitUntil(lambda: task not in LaTeXSourcesTask._running, timeout=10_000)
    qtbot.wait(100)  # a finished signal would be delivered by now

    assert requested == [URL_1], "No download must start after the cancellation"
    assert not folder.exists(), "The task must remove its folder"
    assert finished == []


def test_latex_sources_task_cancelled_after_finishing(tmp_path: Path):
    """
    Once the task has finished, cancel() returns False: the folder must be
    removed by the caller.
    """
    task = LaTeXSourcesTask("text", tmp_path)
    task.run()

    assert not task.cancel()
    assert (tmp_path / "main.tex").exists()
