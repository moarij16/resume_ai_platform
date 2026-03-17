"""
Singleton model loading and optional caching for spaCy and SentenceTransformer.

Lazy-loads models once per process; supports graceful fallback on failure.
"""

from typing import Any, Optional

from ..config import SPACY_MODEL, EMBEDDING_MODEL
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """Centralized model loading with singleton pattern and error recovery."""

    _spacy_model: Any = None
    _sentence_model: Any = None
    _spacy_failed: bool = False
    _sentence_failed: bool = False

    @classmethod
    def get_spacy_model(cls) -> Any:
        """Load and cache spaCy model. Raises OSError if load fails (no fallback for NER)."""
        if cls._spacy_model is not None:
            return cls._spacy_model
        if cls._spacy_failed:
            raise OSError("spaCy model previously failed to load.")
        try:
            import spacy
            cls._spacy_model = spacy.load(SPACY_MODEL)
            logger.debug("Loaded spaCy model: %s", SPACY_MODEL)
            return cls._spacy_model
        except Exception as e:
            cls._spacy_failed = True
            logger.warning("SpaCy model load failed: %s. Use regex fallbacks where available.", e)
            raise OSError(
                f"spaCy model '{SPACY_MODEL}' not found. "
                "Run: python -m spacy download en_core_web_md"
            ) from e

    @classmethod
    def get_sentence_model(cls) -> Any:
        """Load and cache SentenceTransformer model."""
        if cls._sentence_model is not None:
            return cls._sentence_model
        if cls._sentence_failed:
            raise RuntimeError("SentenceTransformer previously failed to load.")
        try:
            from sentence_transformers import SentenceTransformer
            cls._sentence_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.debug("Loaded embedding model: %s", EMBEDDING_MODEL)
            return cls._sentence_model
        except Exception as e:
            cls._sentence_failed = True
            logger.warning("SentenceTransformer load failed: %s", e)
            raise

    @classmethod
    def clear_cache(cls) -> None:
        """Reset cached models (e.g. for tests)."""
        cls._spacy_model = None
        cls._sentence_model = None
        cls._spacy_failed = False
        cls._sentence_failed = False
