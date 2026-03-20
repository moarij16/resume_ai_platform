"""
Public rendering API.

Usage:
    render_pdf(document)                     # uses default template
    render_pdf(document, template="modern")  # explicit template
    render_docx(document)
    render_docx(document, template="modern")

To add a new template register it in services/templates/__init__.py.
"""

from .templates import get_template

_DEFAULT_TEMPLATE = "modern"


def render_pdf(document, template: str = _DEFAULT_TEMPLATE) -> bytes:
    return get_template(template).render_pdf(document)


def render_docx(document, template: str = _DEFAULT_TEMPLATE) -> bytes:
    return get_template(template).render_docx(document)
