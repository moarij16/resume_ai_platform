"""
Structured experience extraction: job titles, companies, dates, duration.
"""

import re
from typing import Any

try:
    import dateparser
except ImportError:
    dateparser = None  # type: ignore[assignment]

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Date pattern: "Jan 2020", "2020 - 2022", "January 2019 – Present", etc.
DATE_RANGE = re.compile(
    r"(\d{4}|\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\s*[-–—to]+\s*"
    r"(present|current|now|\d{4}|\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.IGNORECASE,
)
SINGLE_DATE = re.compile(
    r"(?:^|\s)(\d{4}|\w+\s+\d{4})(?:\s|$|,|\))",
    re.IGNORECASE,
)


def _parse_date(s: str) -> int | None:
    """Return year as int or None."""
    if not s:
        return None
    s = s.strip().lower()
    if s in ("present", "current", "now"):
        from datetime import datetime
        return datetime.now().year
    if dateparser:
        parsed = dateparser.parse(s)
        return parsed.year if parsed else None
    # Fallback: 4-digit year
    match = re.search(r"\b(19|20)\d{2}\b", s)
    return int(match.group(0)) if match else None


def parse_experience(text: str) -> dict[str, Any]:
    """
    Extract job titles, companies, and date ranges from resume text.

    Args:
        text: Full resume or experience section text.

    Returns:
        Dictionary with:
          experiences: list of {title, company, start_year, end_year, duration_years}
          total_years: approximate total years
          employment_gaps: list of gap descriptions (simplified)
    """
    experiences: list[dict[str, Any]] = []
    seen_ranges: set[tuple[int | None, int | None]] = set()

    # Find experience section
    lines = text.split("\n")
    in_experience = False
    block: list[str] = []
    for line in lines:
        if re.search(r"^(?:work\s+)?experience|employment|professional\s+experience", line, re.IGNORECASE):
            in_experience = True
            block = []
            continue
        if in_experience:
            if re.search(r"^education|^skills|^projects", line, re.IGNORECASE):
                in_experience = False
                _parse_block("\n".join(block), experiences, seen_ranges)
                block = []
                continue
            block.append(line)
    if block:
        _parse_block("\n".join(block), experiences, seen_ranges)

    # If no section found, scan full text for date ranges and titles
    if not experiences:
        _parse_block(text, experiences, seen_ranges)

    total_years = 0
    for exp in experiences:
        start = exp.get("start_year")
        end = exp.get("end_year")
        if start and end:
            total_years += min(end - start + 1, 50)
        elif start:
            from datetime import datetime
            total_years += min(datetime.now().year - start + 1, 50)

    gaps: list[str] = []
    sorted_exp = sorted(
        [e for e in experiences if e.get("end_year")],
        key=lambda x: x.get("end_year") or 0,
        reverse=True,
    )
    for i in range(len(sorted_exp) - 1):
        end_curr = sorted_exp[i].get("end_year")
        start_next = sorted_exp[i + 1].get("start_year")
        if end_curr and start_next and start_next - end_curr > 1:
            gaps.append(f"Gap between {end_curr} and {start_next}")

    return {
        "experiences": experiences,
        "total_years": total_years,
        "employment_gaps": gaps,
    }


def _parse_block(block: str, out: list[dict[str, Any]], seen: set[tuple[int | None, int | None]]) -> None:
    """Parse a block of text for job entries with dates."""
    for m in DATE_RANGE.finditer(block):
        start_str, end_str = m.group(1), m.group(2)
        start_year = _parse_date(start_str)
        end_year = _parse_date(end_str)
        key = (start_year, end_year)
        if key in seen:
            continue
        seen.add(key)
        # Try to find title/company before this date (previous line or same line)
        start_pos = m.start()
        prefix = block[max(0, start_pos - 200):start_pos]
        lines_before = [l.strip() for l in prefix.split("\n") if l.strip()]
        title = lines_before[-1][:80] if lines_before else "Unknown"
        company = lines_before[-2][:80] if len(lines_before) >= 2 else ""
        duration = (end_year - start_year + 1) if (start_year and end_year) else None
        out.append({
            "title": title,
            "company": company,
            "start_year": start_year,
            "end_year": end_year,
            "duration_years": duration,
        })
