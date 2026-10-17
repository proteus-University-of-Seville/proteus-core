# ==========================================================================
# File: test_latex_remote_images.py
# Description: pytest file for the download of remote figures done by the
#              LaTeX export strategies of the basic plugin
#              (resources/plugins/basic/export/export_latex.py)
# Date: 07/10/2026
# Version: 0.1
# Author: Amador Durán Toro
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import io
import sys
import threading
import urllib.error
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

# Smallest valid PNG and JPEG headers are enough: they are written as is
PNG_DATA = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG_DATA = b"\xff\xd8\xff\xe0" + b"\x00" * 16

URL_1 = "https://example.org/a_b.jpg?x=1&y=2"
URL_2 = "https://example.org/logo.png"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def mock_urlopen(monkeypatch, responses: dict) -> list:
    """
    Replaces urllib.request.urlopen: each URL returns its bytes or raises
    if its response is an exception. Returns the list of requested URLs.
    """
    requested = []

    def urlopen(request, timeout=None):
        requested.append(request.full_url)
        mock_urlopen.thread_id = threading.get_ident()
        response = responses[request.full_url]
        if isinstance(response, Exception):
            raise response
        return io.BytesIO(response)

    monkeypatch.setattr(export_latex.urllib.request, "urlopen", urlopen)
    return requested


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_remote_images_are_downloaded_once(monkeypatch, tmp_path: Path):
    """
    Remote figures are downloaded to remote/ (once per URL), keeping JPEG
    and PNG files as they are, and replaced by \\includegraphics.
    """
    requested = mock_urlopen(monkeypatch, {URL_1: JPEG_DATA, URL_2: PNG_DATA})
    tex = (
        f"A \\ProteusRemoteImage{{0.25}}{{{URL_1}}}\n"
        f"B \\ProteusRemoteImage{{0.5}}{{{URL_2}}}\n"
        f"C \\ProteusRemoteImage{{0.3}}{{{URL_1}}}\n"
    )

    result = export_latex._replace_remote_images(tex, tmp_path)

    assert result == (
        "A \\includegraphics[width=0.25\\linewidth]{remote/image-1.jpg}\n"
        "B \\includegraphics[width=0.5\\linewidth]{remote/image-2.png}\n"
        "C \\includegraphics[width=0.3\\linewidth]{remote/image-1.jpg}\n"
    )
    assert requested == [URL_1, URL_2], "Each URL must be downloaded once"
    assert (tmp_path / "remote" / "image-1.jpg").read_bytes() == JPEG_DATA
    assert (tmp_path / "remote" / "image-2.png").read_bytes() == PNG_DATA


@pytest.mark.parametrize(
    "response",
    [
        urllib.error.URLError("no network"),
        b"<html>not an image</html>",
    ],
)
def test_remote_image_not_available(monkeypatch, tmp_path: Path, response):
    """
    If the image cannot be downloaded or is not an image, the figure shows
    the escaped URL as a link inside \\ProteusMissingImage.
    """
    mock_urlopen(monkeypatch, {URL_1: response})

    result = export_latex._replace_remote_images(
        f"\\ProteusRemoteImage{{0.25}}{{{URL_1}}}", tmp_path
    )

    assert result == (
        "\\ProteusMissingImage{\\href{https://example.org/a_b.jpg?x=1\\&y=2}"
        "{\\texttt{https://example.org/a\\_b.jpg?x=1\\&y=2}}}"
    )
    assert not (tmp_path / "remote").exists() or not any((tmp_path / "remote").iterdir())


def test_latex_sources_task_runs_in_worker_thread(monkeypatch, tmp_path: Path, qtbot):
    """
    LaTeXSourcesTask downloads the remote figures in a worker thread, writes
    main.tex and reports it with its finished signal, delivered in the
    application thread.
    """
    mock_urlopen(monkeypatch, {URL_1: JPEG_DATA})
    received_in = []

    task = export_latex.LaTeXSourcesTask(f"\\ProteusRemoteImage{{0.25}}{{{URL_1}}}", tmp_path)
    task.signals.finished.connect(lambda *args: received_in.append(threading.get_ident()))

    with qtbot.waitSignal(task.signals.finished, timeout=10_000) as blocker:
        task.start()

    main_file, success = blocker.args
    assert success
    assert Path(main_file) == tmp_path / "main.tex"
    assert (tmp_path / "main.tex").read_text(encoding="utf-8") == (
        "\\includegraphics[width=0.25\\linewidth]{remote/image-1.jpg}"
    )
    assert mock_urlopen.thread_id != threading.get_ident(), "Download must not block the application thread"
    qtbot.waitUntil(lambda: len(received_in) > 0, timeout=5_000)
    assert received_in == [threading.get_ident()], "Signal must be delivered in the application thread"
    qtbot.waitUntil(lambda: task not in export_latex.LaTeXSourcesTask._running, timeout=5_000)
