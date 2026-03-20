"""
Dynamic keyword density: optimal 2–3%, over-stuffing detection, where to add.
"""

import re
from typing import Any

from ..config import (
    OPTIMAL_KEYWORD_DENSITY_PCT,
    KEYWORD_DENSITY_MIN_PCT,
    KEYWORD_DENSITY_MAX_PCT,
)
from ..analyzers.section_detector import detect_sections
from ..utils.logger import get_logger

logger = get_logger(__name__)


def compute_keyword_density(
    resume_text: str,
    critical_keywords: list[str],
    section_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Per-keyword density, optimal target, over-stuffing flag, and safe_locations.
    """
    if not critical_keywords:
        return {}
    sections_result = detect_sections(resume_text)
    sections = sections_result.get("sections", [])
    total_words = len(resume_text.split()) or 1
    result: dict[str, Any] = {}
    for kw in critical_keywords:
        kw_lower = kw.lower()
        count = 0
        by_section: dict[str, int] = {}
        for sec in sections:
            name = (sec.get("name") or "").strip().lower()
            content = sec.get("content") or ""
            words = content.split()
            section_count = sum(1 for w in words if kw_lower in w.lower())
            by_section[name] = section_count
            count += section_count
        current_pct = (count / total_words) * 100.0
        optimal = OPTIMAL_KEYWORD_DENSITY_PCT
        is_over = current_pct > KEYWORD_DENSITY_MAX_PCT
        is_under = current_pct < KEYWORD_DENSITY_MIN_PCT
        need_more = max(0, int((optimal / 100.0) * total_words - count))
        safe_locations: list[str] = []
        for name, c in by_section.items():
            if c == 0 and name in ("work experience", "experience", "projects", "skills"):
                safe_locations.append(f"{name.replace(' ', ' ').title()} section")
        if need_more > 0 and not safe_locations:
            safe_locations.append("Experience or Projects section")
        suggestion = ""
        if is_over:
            suggestion = f"Keyword density ({current_pct:.1f}%) is high; consider reducing repetition to avoid spam detection."
        elif is_under and need_more > 0:
            suggestion = f"Add {need_more} more mention(s) in Experience section" + (
                f" or {', '.join(safe_locations[:2])}." if safe_locations else "."
            )
        result[kw] = {
            "current_density_pct": round(current_pct, 2),
            "optimal_density_pct": optimal,
            "mention_count": count,
            "is_overstuffed": is_over,
            "suggestion": suggestion,
            "safe_locations": safe_locations[:5],
        }
    return result
