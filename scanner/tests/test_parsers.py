"""Unit tests for resume parser."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import pytest
from scanner.parsers.resume_parser import parse_resume


def test_parse_resume_nonexistent():
    """Raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_resume(Path("/nonexistent/resume.pdf"))


def test_parse_resume_unsupported_type(tmp_path):
    """Raises ValueError for unsupported file type."""
    f = tmp_path / "file.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_resume(f)
