"""
Template registry.

To register a new template:
  1. Import its class here
  2. Add an entry to TEMPLATES

The key is what callers pass as template_name (e.g. "modern").
"""

from .base import ResumeTemplate
from .modern import ModernTemplate

TEMPLATES: dict[str, type[ResumeTemplate]] = {
    "modern": ModernTemplate,
}


def get_template(name: str) -> ResumeTemplate:
    cls = TEMPLATES.get(name)
    if cls is None:
        available = ", ".join(TEMPLATES)
        raise ValueError(f"Unknown resume template '{name}'. Available: {available}")
    return cls()
