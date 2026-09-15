"""Launcher used when packaged with PyInstaller.

Boots Streamlit against `app.py` and opens the default browser at the
correct URL. Also works when run from source: `python run_app.py`.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


PORT = 8501


def _resource_path(rel: str) -> str:
    """Resolve a file path both in source mode and inside a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base) / rel)
    return str(Path(__file__).resolve().parent / rel)


def _open_browser_when_ready() -> None:
    # Give the Streamlit server a moment to come up before opening the browser.
    time.sleep(2.0)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass


def main() -> None:
    app_path = _resource_path("app.py")

    # Make sure Streamlit does not try to open a browser itself; we do it below.
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")

    # Invoke the Streamlit CLI programmatically. This is the most version-
    # stable entry point across Streamlit releases.
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        f"--server.port={PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]

    threading.Thread(target=_open_browser_when_ready, daemon=True).start()

    from streamlit.web import cli as stcli

    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
