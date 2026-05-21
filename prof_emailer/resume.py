from __future__ import annotations

from pathlib import Path


def extract_resume_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported by --resume. Use --resume-text-file for text.")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is missing. Run: pip install -r requirements.txt") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("No selectable text was found in the resume PDF.")
    return text
