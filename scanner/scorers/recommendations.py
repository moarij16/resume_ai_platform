"""
Actionable recommendations with severity and estimated impact.
No generic "Add AWS"; specific actions with locations and suggested text.
"""

from typing import Any

from ..config import SECTION_WEIGHTS_SCORING
from ..utils.logger import get_logger

logger = get_logger(__name__)

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"


def build_actionable_recommendations(
    *,
    missing_skills: list[str],
    resume_sections: list[dict[str, Any]] | None = None,
    weak_bullets: list[str] | None = None,
    keyword_density: dict[str, Any] | None = None,
    jd_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Build recommendations with severity, specific actions, and estimated impact.
    """
    recs: list[dict[str, Any]] = []
    if missing_skills:
        for skill in missing_skills[:5]:
            recs.append({
                "severity": SEVERITY_HIGH if len(missing_skills) >= 3 else SEVERITY_MEDIUM,
                "title": f"Missing: {skill}",
                "actions": [
                    f'Add to Skills section: "{skill}"',
                    f'Enhance a bullet in Experience: e.g. "Used {skill} to..."',
                ],
                "estimated_impact_pct": 12,
            })
    if weak_bullets:
        recs.append({
            "severity": SEVERITY_MEDIUM,
            "title": "Weak bullet points",
            "actions": [
                "Start with an action verb (Led, Developed, Increased)",
                "Add at least one metric (%, $, time, scale)",
                f"Rewrite example: \"{weak_bullets[0][:60]}...\" with a result",
            ],
            "estimated_impact_pct": 8,
        })
    if keyword_density:
        for kw, data in list(keyword_density.items())[:3]:
            if data.get("is_overstuffed"):
                recs.append({
                    "severity": SEVERITY_LOW,
                    "title": f"Keyword density high for '{kw}'",
                    "actions": [data.get("suggestion", "Reduce repetition to avoid spam detection.")],
                    "estimated_impact_pct": 0,
                })
            elif data.get("suggestion"):
                recs.append({
                    "severity": SEVERITY_MEDIUM,
                    "title": f"Add more '{kw}'",
                    "actions": [
                        data.get("suggestion", ""),
                        "Safe locations: " + ", ".join(data.get("safe_locations", [])[:3]),
                    ],
                    "estimated_impact_pct": 6,
                })
    if not recs:
        recs.append({
            "severity": SEVERITY_LOW,
            "title": "Resume looks strong",
            "actions": ["Consider adding 1–2 quantified achievements if space allows."],
            "estimated_impact_pct": 0,
        })
    return sorted(recs, key=lambda x: (["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(x["severity"]), -x.get("estimated_impact_pct", 0)))
