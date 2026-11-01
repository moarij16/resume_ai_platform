"""
Dual similarity: TF-IDF cosine and semantic (SentenceTransformer).
"""

from typing import Optional

from ..config import DEFAULT_TFIDF_WEIGHT, DEFAULT_SEMANTIC_WEIGHT
from ..utils.logger import get_logger
from ..utils.model_manager import ModelManager

logger = get_logger(__name__)


def _get_sentence_model():
    return ModelManager.get_sentence_model()


def compute_tfidf_similarity(text1: str, text2: str) -> float:
    """
    TF-IDF vectorization + cosine similarity between two texts.

    Args:
        text1: First document (e.g. resume).
        text2: Second document (e.g. job description).

    Returns:
        Similarity score in [0, 1].
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError as e:
        raise ImportError("scikit-learn required for TF-IDF. pip install scikit-learn") from e
    if not text1.strip() or not text2.strip():
        return 0.0
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    try:
        matrix = vectorizer.fit_transform([text1, text2])
    except Exception:
        return 0.0
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return max(0.0, min(1.0, float(sim)))


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Semantic similarity using SentenceTransformer embeddings.

    Args:
        text1: First document.
        text2: Second document.

    Returns:
        Similarity score in [0, 1].
    """
    model = _get_sentence_model()
    # Truncate to avoid token limits
    t1 = text1[:8000].strip()
    t2 = text2[:8000].strip()
    if not t1 or not t2:
        return 0.0
    import numpy as np
    e1 = model.encode(t1, convert_to_tensor=False)
    e2 = model.encode(t2, convert_to_tensor=False)
    if isinstance(e1, list):
        e1 = np.array(e1)
    if isinstance(e2, list):
        e2 = np.array(e2)
    if e1.ndim == 1:
        e1 = e1.reshape(1, -1)
    if e2.ndim == 1:
        e2 = e2.reshape(1, -1)
    dot = np.dot(e1, e2.T)[0][0]
    norm = np.linalg.norm(e1) * np.linalg.norm(e2)
    sim = (dot / norm).item() if norm > 0 else 0.0
    return max(0.0, min(1.0, float(sim)))


def hybrid_similarity(
    text1: str,
    text2: str,
    tfidf_weight: float = DEFAULT_TFIDF_WEIGHT,
) -> float:
    """
    Weighted combination of TF-IDF and semantic similarity.

    Args:
        text1: First document.
        text2: Second document.
        tfidf_weight: Weight for TF-IDF; semantic gets (1 - tfidf_weight).

    Returns:
        Combined score in [0, 1].
    """
    try:
        tfidf = compute_tfidf_similarity(text1, text2)
    except Exception:
        tfidf = 0.0
    try:
        semantic = compute_semantic_similarity(text1, text2)
    except Exception:
        semantic = 0.0
    return tfidf_weight * tfidf + (1.0 - tfidf_weight) * semantic
