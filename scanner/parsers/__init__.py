"""
Resume parsers for PDF and DOCX extraction.

Exposes the main parse_resume function for use by the scanner pipeline.
"""

from .resume_parser import parse_resume

__all__ = ["parse_resume"]
