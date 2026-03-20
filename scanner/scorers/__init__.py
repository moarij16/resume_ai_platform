"""
Similarity and scoring engines for ATS matching.

Provides TF-IDF/semantic similarity and ATS compatibility scoring.
"""

from .similarity_engine import (
    compute_tfidf_similarity,
    compute_semantic_similarity,
    hybrid_similarity,
)
from .ats_scorer import score_resume_vs_jd

__all__ = [
    "compute_tfidf_similarity",
    "compute_semantic_similarity",
    "hybrid_similarity",
    "score_resume_vs_jd",
]
