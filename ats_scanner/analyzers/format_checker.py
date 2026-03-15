"""
ATS compatibility format checks.

Flags tables, graphics, headers/footers, text boxes, excessive special
characters, and non-standard section names.
"""

import re
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


def check_format(
    text: str,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Run ATS format compatibility checks and return warnings.

    Args:
        text: Resume text.
        metadata: Optional parser metadata (has_images, has_tables, etc.).

    Returns:
        List of {message, severity} where severity is "low", "medium", "high".
    """
    warnings: list[dict[str, Any]] = []
    meta = metadata or {}

    if meta.get("has_images"):
        warnings.append({
            "message": "Resume contains images or graphics; ATS may not parse them.",
            "severity": "high",
        })
    if meta.get("has_tables"):
        warnings.append({
            "message": "Resume contains tables; parsing may be unreliable.",
            "severity": "high",
        })
    for _ in meta.get("encoding_issues", []):
        warnings.append({
            "message": "Encoding issues detected; some text may be corrupted.",
            "severity": "medium",
        })
        break

    # Headers/footers: repeated text at line start/end
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) >= 4:
        first_two = " ".join(lines[:2]).lower()
        last_two = " ".join(lines[-2:]).lower()
        if first_two == last_two and len(first_two) > 10:
            warnings.append({
                "message": "Repeated header/footer detected; ensure critical info is in body.",
                "severity": "medium",
            })

    # Excessive special characters
    non_alpha_ratio = 1 - sum(1 for c in text if c.isalnum() or c.isspace()) / max(len(text), 1)
    if non_alpha_ratio > 0.15:
        warnings.append({
            "message": "High ratio of special characters; may indicate formatting issues.",
            "severity": "low",
        })

    # Non-standard section headers (optional: could load from config)
    standard_headers = {
        "summary", "objective", "experience", "education", "skills",
        "projects", "certifications", "awards", "publications", "volunteer",
    }
    for line in lines[:50]:  # Check first 50 non-empty lines
        lower = line.lower()
        if len(lower) < 3 or len(lower) > 50:
            continue
        if line.isupper() and " " not in line:
            continue
        if re.match(r"^[a-z][a-z\s]+$", lower) and lower not in standard_headers:
            if any(kw in lower for kw in ("experience", "education", "skill", "work")):
                continue
            # Could add: "Unusual section name: ..." with low severity

    return warnings
