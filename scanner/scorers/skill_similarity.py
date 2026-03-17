"""
Multi-tier skill matching: exact, synonym, related, category.
Uses local embeddings for semantic similarity.
"""

from typing import Any, Optional

from ..utils.logger import get_logger
from ..utils.acronyms import get_skill_synonyms

logger = get_logger(__name__)

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from ..utils.model_manager import ModelManager
        _embedding_model = ModelManager.get_sentence_model()
    return _embedding_model


def calculate_skill_similarity(resume_skill: str, jd_skill: str) -> float:
    """
    Return confidence score 0–1: exact (1.0), synonym (~0.95), related (~0.7), category (~0.8).
    """
    r = resume_skill.strip().lower()
    j = jd_skill.strip().lower()
    if r == j:
        return 1.0
    r_synonyms = set(s.lower() for s in get_skill_synonyms(r))
    j_synonyms = set(s.lower() for s in get_skill_synonyms(j))
    if r_synonyms & j_synonyms:
        return 0.95
    if r in j_synonyms or j in r_synonyms:
        return 0.95
    try:
        model = _get_embedding_model()
        import numpy as np
        e1 = model.encode(r, convert_to_tensor=False)
        e2 = model.encode(j, convert_to_tensor=False)
        if isinstance(e1, list):
            e1 = np.array(e1)
        if isinstance(e2, list):
            e2 = np.array(e2)
        e1 = e1.reshape(1, -1) if e1.ndim == 1 else e1
        e2 = e2.reshape(1, -1) if e2.ndim == 1 else e2
        dot = np.dot(e1, e2.T)[0][0]
        norm = np.linalg.norm(e1) * np.linalg.norm(e2)
        sim = (dot / norm).item() if norm > 0 else 0.0
        # Map cosine to our tier: 0.9+ -> 0.9, 0.7+ -> 0.8, 0.5+ -> 0.7
        if sim >= 0.9:
            return 0.9
        if sim >= 0.75:
            return 0.8
        if sim >= 0.5:
            return 0.7
        return max(0.0, sim)
    except Exception as e:
        logger.debug("Embedding similarity failed: %s", e)
        return 0.0
