"""
Resume parser for PDF and DOCX extraction.

Detects file type, extracts raw text with layout awareness, and flags
ATS-unfriendly elements (tables, images, text boxes, etc.).
"""

import re
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


def _extract_pdf(file_path: Path) -> tuple[str, dict[str, Any]]:
    """Extract text and metadata from a PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError(
            "PDF support requires pymupdf. Install with: pip install pymupdf"
        ) from e

    text_parts: list[str] = []
    page_count = 0
    has_images = False
    has_tables = False
    encoding_issues: list[str] = []

    with fitz.open(file_path) as doc:
        page_count = len(doc)
        for page_num in range(page_count):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        line_texts = []
                        for span in line.get("spans", []):
                            raw = span.get("text", "")
                            try:
                                if raw.encode("utf-8").decode("utf-8") != raw:
                                    encoding_issues.append(
                                        f"Page {page_num + 1}: non-UTF-8 sequence"
                                    )
                            except (UnicodeDecodeError, UnicodeEncodeError):
                                encoding_issues.append(
                                    f"Page {page_num + 1}: encoding error"
                                )
                            line_texts.append(raw)
                        text_parts.append(" ".join(line_texts))
                elif block.get("type") == 1:  # Image block
                    has_images = True
            # Heuristic: multiple small text blocks in a grid suggest tables
            if len(blocks) > 8 and page_count == 1:
                has_tables = True

    text = "\n".join(text_parts).strip()
    if not text and page_count > 0:
        encoding_issues.append("No text extracted; PDF may be image-based or encrypted")
    metadata = {
        "has_images": has_images,
        "has_tables": has_tables,
        "encoding_issues": encoding_issues,
    }
    return text, metadata


def _extract_docx(file_path: Path) -> tuple[str, dict[str, Any]]:
    """Extract text and metadata from a DOCX using python-docx."""
    try:
        from docx import Document
    except ImportError as e:
        raise ImportError(
            "DOCX support requires python-docx. Install with: pip install python-docx"
        ) from e

    doc = Document(file_path)
    text_parts: list[str] = []
    has_tables = False
    has_images = False
    encoding_issues: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            text_parts.append(text)
    for table in doc.tables:
        has_tables = True
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_texts:
                text_parts.append(" | ".join(row_texts))

    try:
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                has_images = True
                break
    except Exception:
        pass

    try:
        text = "\n".join(text_parts).strip()
        text.encode("utf-8").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        encoding_issues.append("DOCX contains non-UTF-8 text")

    metadata = {
        "has_images": has_images,
        "has_tables": has_tables,
        "encoding_issues": encoding_issues,
    }
    return text, metadata


def parse_resume(file_path: Path) -> dict[str, Any]:
    """
    Parse a resume file (PDF or DOCX) and return extracted text with metadata.

    Detects file type, extracts raw text with layout awareness, and reports
    ATS-unfriendly elements (tables, images, encoding issues).

    Args:
        file_path: Path to the resume file (PDF or DOCX).

    Returns:
        Dictionary with:
          - text: Extracted raw text.
          - metadata: file_type, page_count (PDF only), has_images, has_tables,
            encoding_issues (list of warning messages).

    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If file type is not PDF or DOCX.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        file_type = "pdf"
        text, meta = _extract_pdf(path)
        try:
            import fitz
            with fitz.open(path) as doc:
                page_count = len(doc)
        except Exception:
            page_count = 0
        metadata = {
            "file_type": file_type,
            "page_count": page_count,
            "has_images": meta.get("has_images", False),
            "has_tables": meta.get("has_tables", False),
            "encoding_issues": meta.get("encoding_issues", []),
        }
    elif suffix in (".docx", ".doc"):
        file_type = "docx"
        text, meta = _extract_docx(path)
        metadata = {
            "file_type": file_type,
            "page_count": 0,  # DOCX page count not trivial without rendering
            "has_images": meta.get("has_images", False),
            "has_tables": meta.get("has_tables", False),
            "encoding_issues": meta.get("encoding_issues", []),
        }
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. Use PDF (.pdf) or Word (.docx)."
        )

    for issue in metadata.get("encoding_issues", []):
        logger.warning("Resume encoding: %s", issue)
    if metadata.get("has_images"):
        logger.warning("Resume contains images; ATS may not parse them.")
    if metadata.get("has_tables"):
        logger.warning("Resume contains tables; ATS parsing may be affected.")

    return {"text": text, "metadata": metadata}
