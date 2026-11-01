"""
Resume section identification using regex and heading patterns.

Detects standard sections: Summary, Experience, Education, Skills,
Projects, Certifications, Awards, Publications, Volunteer.
"""

import re
from typing import Any

from ..config import REQUIRED_SECTIONS, OPTIONAL_SECTIONS
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Common section header patterns (case-insensitive, start of line or after newline)
SECTION_PATTERNS = [
    (r"^(?:professional\s+)?summary\b", "professional summary"),
    (r"^(?:career\s+)?objective\b", "objective"),
    (r"^(?:work\s+)?experience\b", "work experience"),
    (r"^employment\s+history\b", "work experience"),
    (r"^professional\s+experience\b", "work experience"),
    (r"^education\b", "education"),
    (r"^(?:technical\s+)?skills\b", "skills"),
    (r"^core\s+competencies\b", "skills"),
    (r"^projects\b", "projects"),
    (r"^certifications?\b", "certifications"),
    (r"^licenses?\b", "licenses"),
    (r"^awards?\b", "awards"),
    (r"^achievements?\b", "achievements"),
    (r"^publications?\b", "publications"),
    (r"^volunteer\b", "volunteer"),
    (r"^languages?\b", "languages"),
]


def detect_sections(text: str) -> dict[str, Any]:
    """
    Identify resume sections and return their boundaries and content.

    Args:
        text: Full resume text.

    Returns:
        Dictionary with:
          sections: list of {name, start, end, content}
          section_names: list of detected section names
          required_present: list of required section names found
          optional_present: list of optional section names found
    """
    sections: list[dict[str, Any]] = []
    lines = text.split("\n")
    current_section: str | None = None
    current_start = 0
    current_lines: list[str] = []

    def flush_section(end_idx: int) -> None:
        nonlocal current_section, current_lines
        if current_section:
            content = "\n".join(current_lines).strip()
            sections.append({
                "name": current_section,
                "start": current_start,
                "end": end_idx,
                "content": content,
            })
        current_section = None
        current_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if current_section:
                current_lines.append(line)
            continue
        matched = False
        for pattern, section_name in SECTION_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                flush_section(i)
                current_section = section_name
                current_start = i
                current_lines = []
                matched = True
                break
        if not matched and current_section:
            current_lines.append(line)

    flush_section(len(lines))
    section_names = [s["name"] for s in sections]
    required_present = [s for s in section_names if s in REQUIRED_SECTIONS]
    optional_present = [s for s in section_names if s in OPTIONAL_SECTIONS]

    return {
        "sections": sections,
        "section_names": section_names,
        "required_present": required_present,
        "optional_present": optional_present,
    }
