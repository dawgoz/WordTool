"""Convert a .docx file to .pdf on Windows or macOS.

Preferred backend: `docx2pdf` (uses Microsoft Word via COM on Windows or
AppleScript on macOS). Falls back to LibreOffice `soffice --headless` if
Word is not available.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


class PdfConversionError(RuntimeError):
    """Raised when neither backend can produce a PDF."""


def _try_docx2pdf(docx_path: Path, pdf_path: Path) -> bool:
    try:
        from docx2pdf import convert  # type: ignore[import-untyped]
    except Exception:
        return False

    try:
        # docx2pdf writes next to the input if given a file path; pass the
        # explicit output path to force placement.
        convert(str(docx_path), str(pdf_path))
    except Exception:
        return False
    return pdf_path.exists()


def _find_soffice() -> str | None:
    candidate = shutil.which("soffice") or shutil.which("libreoffice")
    if candidate:
        return candidate

    if sys.platform == "darwin":
        mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if mac_path.exists():
            return str(mac_path)
    elif sys.platform.startswith("win"):
        for env in ("ProgramFiles", "ProgramFiles(x86)"):
            import os

            base = os.environ.get(env)
            if not base:
                continue
            win_path = Path(base) / "LibreOffice" / "program" / "soffice.exe"
            if win_path.exists():
                return str(win_path)
    return None


def _try_libreoffice(docx_path: Path, pdf_path: Path) -> bool:
    soffice = _find_soffice()
    if not soffice:
        return False

    outdir = pdf_path.parent
    try:
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(outdir),
                str(docx_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

    produced = outdir / (docx_path.stem + ".pdf")
    if produced.exists() and produced != pdf_path:
        produced.replace(pdf_path)
    return pdf_path.exists()


def convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    """Convert `docx_path` to `pdf_path`. Returns the PDF path on success.

    Backend preference:
    * macOS: LibreOffice first, then `docx2pdf` (which drives Word via
      AppleScript and triggers macOS TCC/Automation prompts).
    * Everywhere else: `docx2pdf` first (uses Word via COM on Windows),
      then LibreOffice.
    """
    docx_path = Path(docx_path)
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "darwin":
        backends = (_try_libreoffice, _try_docx2pdf)
    elif sys.platform.startswith("win"):
        backends = (_try_docx2pdf, _try_libreoffice)
    else:
        # Linux / server: docx2pdf is not usable (no Word), go straight to LibreOffice.
        backends = (_try_libreoffice,)

    for backend in backends:
        if backend(docx_path, pdf_path):
            return pdf_path

    if sys.platform == "darwin":
        raise PdfConversionError(
            "Could not convert DOCX to PDF on macOS.\n"
            "Recommended: install LibreOffice (e.g. `brew install --cask "
            "libreoffice`) — it avoids the macOS Automation permission "
            "dialogs entirely.\n"
            "Alternative: install Microsoft Word for Mac and, when prompted, "
            "allow this app to control Word in "
            "System Settings → Privacy & Security → Automation."
        )

    if sys.platform.startswith("linux"):
        raise PdfConversionError(
            "Could not convert DOCX to PDF. LibreOffice (`soffice`) was not "
            "found or failed. On the server image install `libreoffice-core` "
            "and `libreoffice-writer` (already handled by the provided "
            "Dockerfile)."
        )

    raise PdfConversionError(
        "Could not convert DOCX to PDF. Install Microsoft Word "
        "(recommended on Windows) or LibreOffice, then try again."
    )
