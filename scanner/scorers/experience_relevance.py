"""
Experience relevance: title alignment, recency decay, career progression.
"""

from datetime import datetime
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

_title_embedding_cache: dict[str, Any] = {}
_embed_model = None


def _get_model():
    global _embed_model
    if _embed_model is None:
        try:
            from ..utils.model_manager import ModelManager
            _embed_model = ModelManager.get_sentence_model()
        except Exception:
            return None
    return _embed_model


def _title_similarity(title1: str, title2: str) -> float:
    """Compare two job titles (0-1)."""
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    if t1 == t2:
        return 1.0
    words1 = set(t1.split())
    words2 = set(t2.split())
    if words1 & words2:
        return 0.7 + 0.2 * len(words1 & words2) / max(len(words1 | words2), 1)
    model = _get_model()
    if model is None:
        return 0.0
    try:
        import numpy as np
        e1 = model.encode(t1, convert_to_tensor=False)
        e2 = model.encode(t2, convert_to_tensor=False)
        e1 = np.array(e1).reshape(1, -1) if hasattr(e1, "__len__") else e1
        e2 = np.array(e2).reshape(1, -1) if hasattr(e2, "__len__") else e2
        dot = np.dot(e1, e2.T)[0][0]
        norm = np.linalg.norm(e1) * np.linalg.norm(e2)
        return max(0.0, min(1.0, (dot / norm).item() if norm > 0 else 0))
    except Exception:
        return 0.0


def _calculate_recency_factor(experiences: list[dict[str, Any]]) -> float:
    """More recent roles weighted higher. Returns 0-1."""
    if not experiences:
        return 0.0
    current_year = datetime.now().year
    total_weight = 0.0
    total_years = 0.0
    for exp in experiences:
        end = exp.get("end_year") or current_year
        start = exp.get("start_year") or end
        years = max(0, end - start + 1)
        # Recency: weight by how recent the end year is
        years_ago = current_year - end
        weight = max(0.3, 1.0 - years_ago * 0.1)
        total_weight += weight * years
        total_years += years
    if total_years <= 0:
        return 0.5
    return min(1.0, total_weight / total_years)


def _detect_career_growth(experiences: list[dict[str, Any]]) -> float:
    """Simple progression: seniority keywords in titles over time. Returns 0-1."""
    seniority = ["junior", "senior", "lead", "principal", "staff", "architect", "manager", "director", "head", "vp", "chief"]
    if len(experiences) < 2:
        return 0.5
    levels = []
    for exp in experiences:
        title = (exp.get("title") or "").lower()
        level = 0
        for i, kw in enumerate(seniority):
            if kw in title:
                level = i + 1
                break
        levels.append(level)
    if not levels:
        return 0.5
    # Positive trend: later roles have higher level
    improvements = sum(1 for i in range(1, len(levels)) if levels[i] > levels[i - 1])
    return min(1.0, 0.5 + 0.5 * (improvements / max(len(levels) - 1, 1)))


def score_experience_relevance(
    resume_jobs: list[dict[str, Any]],
    jd_text: str,
    jd_title: str | None = None,
) -> dict[str, Any]:
    """
    Compare resume job titles to JD, recency weight, career progression.
    Returns combined_score (0-1), title_match, recency_weight, progression_score.
    """
    if not resume_jobs:
        return {
            "combined_score": 0.0,
            "title_match": 0.0,
            "recency_weight": 0.0,
            "progression_score": 0.5,
        }
    # Extract JD title if not provided (first line or "title:" pattern)
    if not jd_title or not jd_title.strip():
        for line in jd_text.split("\n")[:5]:
            line = line.strip()
            if line and len(line) < 80 and not line.startswith("http"):
                jd_title = line
                break
        jd_title = jd_title or "Software Engineer"
    title_scores = [_title_similarity(job.get("title") or "", jd_title) for job in resume_jobs]
    title_match = max(title_scores) if title_scores else 0.0
    recency_weight = _calculate_recency_factor(resume_jobs)
    progression = _detect_career_growth(resume_jobs)
    combined = 0.5 * title_match + 0.3 * recency_weight + 0.2 * progression
    return {
        "combined_score": min(1.0, combined),
        "title_match": round(title_match, 3),
        "recency_weight": round(recency_weight, 3),
        "progression_score": round(progression, 3),
    }
