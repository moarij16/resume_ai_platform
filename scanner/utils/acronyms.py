"""
Synonym and acronym expansion for better skill/keyword matching.
"""

import json
from pathlib import Path
from typing import Any

from ..config import SYNONYMS_PATH
from ..utils.logger import get_logger

logger = get_logger(__name__)

_synonyms_data: dict[str, Any] | None = None


def _load_synonyms() -> dict[str, Any]:
    global _synonyms_data
    if _synonyms_data is not None:
        return _synonyms_data
    path = Path(SYNONYMS_PATH)
    if not path.exists():
        _synonyms_data = {"acronyms": {}, "skill_synonyms": {}}
        return _synonyms_data
    try:
        with open(path, encoding="utf-8") as f:
            _synonyms_data = json.load(f)
    except Exception as e:
        logger.warning("Could not load synonyms: %s", e)
        _synonyms_data = {"acronyms": {}, "skill_synonyms": {}}
    return _synonyms_data


def expand_acronyms(text: str) -> str:
    """
    Replace known acronyms with full forms for better matching.
    Expands in-place (first occurrence of each acronym in the mapping).
    """
    data = _load_synonyms()
    acronyms = data.get("acronyms", {})
    result = text
    for short, forms in acronyms.items():
        if not forms:
            continue
        full = forms[0] if isinstance(forms[0], str) else str(forms[0])
        # Word-boundary replacement so we don't break mid-word
        import re
        pattern = re.compile(r"\b" + re.escape(short) + r"\b", re.IGNORECASE)
        result = pattern.sub(full, result, count=1)
    return result


def get_skill_synonyms(skill: str) -> list[str]:
    """Return all known synonyms/variations for a skill (e.g. 'react' -> ['React', 'React.js', ...])."""
    data = _load_synonyms()
    synonyms = data.get("skill_synonyms", {})
    key = skill.lower().strip()
    if key in synonyms:
        return list(synonyms[key]) if isinstance(synonyms[key], list) else [synonyms[key]]
    acronyms = data.get("acronyms", {})
    if key.upper() in acronyms:
        return list(acronyms[key.upper()]) if isinstance(acronyms[key.upper()], list) else [acronyms[key.upper()]]
    return [skill]
