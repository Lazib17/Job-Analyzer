"""
Resume text extraction from PDF and DOCX files.
"""

import logging
from pathlib import Path

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def extract_text_from_pdf(file_path: str) -> str:
    """Extract plain text from a PDF resume."""
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def extract_text_from_docx(file_path: str) -> str:
    """Extract plain text from a DOCX resume."""
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_resume_text(file_path: str) -> str:
    """
    Extract text from a resume file based on extension.
    Raises ValueError for unsupported file types.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in {".docx", ".doc"}:
        return extract_text_from_docx(file_path)
    raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")


def validate_resume_file(filename: str) -> str:
    """Validate file extension and return normalized extension."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return ext
