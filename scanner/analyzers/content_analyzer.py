"""
Bullet point quality analysis: action verbs, metrics, STAR, weak phrases.
"""

import re
from pathlib import Path
from typing import Any

from ..config import ACTION_VERBS_PATH
from ..utils.logger import get_logger

logger = get_logger(__name__)

_action_verbs: set[str] = set()


def _load_action_verbs() -> set[str]:
    global _action_verbs
    if _action_verbs:
        return _action_verbs
    path = Path(ACTION_VERBS_PATH)
    if path.exists():
        try:
            import json
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for category_verbs in data.values():
                if isinstance(category_verbs, list):
                    _action_verbs.update(v.strip().lower() for v in category_verbs)
                elif isinstance(category_verbs, dict):
                    for v in category_verbs.values():
                        if isinstance(v, list):
                            _action_verbs.update(x.strip().lower() for x in v)
            if not _action_verbs:
                _action_verbs = _default_action_verbs()
        except Exception as e:
            logger.warning("Could not load action verbs: %s", e)
            _action_verbs = _default_action_verbs()
    else:
        _action_verbs = _default_action_verbs()
    return _action_verbs


def _default_action_verbs() -> set[str]:
    return {
        "led", "managed", "developed", "implemented", "designed", "created",
        "achieved", "increased", "reduced", "improved", "delivered", "built",
        "established", "coordinated", "analyzed", "evaluated", "presented",
    }


WEAK_PHRASES = [
    r"\bresponsible\s+for\b",
    r"\bduties\s+included\b",
    r"\bwork(ed)?\s+on\b",
    r"\bhelped\s+with\b",
    r"\bvarious\b",
    r"\bstuff\b",
    r"\bthings\b",
]
METRIC_PATTERN = re.compile(
    r"\d+%|\$\d|%\s*increase|\d+\s*(?:years?|months?|people|users?|clients?)|"
    r"\d+x\s*improvement|by\s*\d+|reduced\s+by|increased\s+by",
    re.IGNORECASE,
)
BULLET_START = re.compile(r"^[\s•\-*]\s*", re.MULTILINE)

# Achievement patterns: percentage, dollar, time, scale (for STAR/metric extraction)
ACHIEVEMENT_PATTERNS = {
    "percentage": re.compile(r"\d+%"),
    "dollar": re.compile(r"\$[\d,]+[KMB]?"),
    "time": re.compile(r"\d+\s*(?:hours?|days?|weeks?|months?|years?)", re.I),
    "scale": re.compile(r"\d+[KMB]?\+?\s*(?:users?|customers?|transactions?|revenue|team)", re.I),
}
IMPACT_VERBS = re.compile(
    r"\b(increased|reduced|improved|decreased|accelerated|optimized|grew|delivered|achieved|exceeded)\b",
    re.I,
)


def analyze_bullets(text: str) -> dict[str, Any]:
    """
    Analyze bullet points for action verbs, metrics, and weak phrasing.

    Returns:
        total_bullets, bullets_with_action_verbs, bullets_with_metrics,
        weak_bullets, strong_bullets, avg_bullet_length.
    """
    verbs = _load_action_verbs()
    bullet_lines = [
        BULLET_START.sub("", line).strip()
        for line in text.split("\n")
        if line.strip() and re.match(r"^[\s•\-*]\s*\S", line.strip())
    ]
    if not bullet_lines:
        # Fallback: lines that look like bullets (short, sentence-like)
        for line in text.split("\n"):
            s = line.strip()
            if 10 <= len(s) <= 200 and s[0].isupper():
                bullet_lines.append(s)
    total = len(bullet_lines)
    with_verbs = 0
    with_metrics = 0
    weak: list[str] = []
    strong: list[str] = []
    lengths: list[int] = []

    for line in bullet_lines:
        words = line.split()
        lengths.append(len(words))
        first_word = words[0].lower() if words else ""
        if first_word in verbs:
            with_verbs += 1
        if METRIC_PATTERN.search(line):
            with_metrics += 1
        is_weak = any(re.search(p, line, re.IGNORECASE) for p in WEAK_PHRASES)
        if is_weak:
            weak.append(line[:120])
        elif (first_word in verbs or METRIC_PATTERN.search(line)) and len(line) > 30:
            strong.append(line[:120])
    avg_len = sum(lengths) // max(len(lengths), 1) if lengths else 0

    # Achievement pattern extraction
    extracted_metrics: dict[str, list[str]] = {"percentage": [], "dollar": [], "time": [], "scale": []}
    for line in bullet_lines:
        for key, pat in ACHIEVEMENT_PATTERNS.items():
            for m in pat.finditer(line):
                extracted_metrics.setdefault(key, []).append(m.group(0))
    impact_verb_count = sum(1 for line in bullet_lines if IMPACT_VERBS.search(line))

    return {
        "total_bullets": total,
        "bullets_with_action_verbs": with_verbs,
        "bullets_with_metrics": with_metrics,
        "weak_bullets": weak[:15],
        "strong_bullets": strong[:15],
        "avg_bullet_length": avg_len,
        "achievement_patterns": {k: list(dict.fromkeys(v))[:10] for k, v in extracted_metrics.items()},
        "impact_verb_count": impact_verb_count,
    }
