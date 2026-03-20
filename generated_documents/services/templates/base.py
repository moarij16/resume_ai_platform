"""
Abstract base class for resume document templates.

To add a new template:
  1. Subclass ResumeTemplate in a new file under templates/
  2. Implement render_pdf() and render_docx()
  3. Register the class in templates/__init__.py
"""

import json
from abc import ABC, abstractmethod


class ResumeTemplate(ABC):
    """
    Contract every resume template must satisfy.

    Both methods receive a GeneratedDocument instance whose
    document_content is a JSON string with keys:
      summary, experience, education, skills, improvements_made
    """

    @abstractmethod
    def render_pdf(self, document) -> bytes:
        """Return the resume rendered as a PDF byte string."""

    @abstractmethod
    def render_docx(self, document) -> bytes:
        """Return the resume rendered as a DOCX byte string."""

    # ── Shared utilities available to all templates ────────────────────────

    @staticmethod
    def parse_content(document_content: str) -> dict:
        try:
            return json.loads(document_content)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def full_name(user) -> str:
        parts = [user.first_name, user.last_name]
        name = " ".join(p for p in parts if p).strip()
        return name or user.email
