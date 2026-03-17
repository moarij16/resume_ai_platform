"""
NLP text preprocessing pipeline using spaCy.

Provides sentence segmentation, tokenization, lemmatization, POS tagging,
and named entity recognition for resume text. Uses ModelManager singleton;
falls back to regex when spaCy fails.
"""

import re
from typing import Any, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


def _get_nlp():
    """Load and cache the spaCy model via ModelManager."""
    from ..utils.model_manager import ModelManager
    return ModelManager.get_spacy_model()


def preprocess_text(text: str, preserve_case: bool = False) -> str:
    """
    Run preprocessing pipeline: tokenize, lemmatize, remove stopwords.
    Falls back to simple tokenization if spaCy fails.
    """
    if not text or not text.strip():
        return ""
    try:
        nlp = _get_nlp()
        doc = nlp(text[:1000000])
        tokens = []
        for tok in doc:
            if tok.is_stop and tok.pos_ != "NUM":
                continue
            if tok.is_punct or tok.is_space:
                continue
            lemma = tok.lemma_.strip()
            if not lemma:
                continue
            if not preserve_case:
                lemma = lemma.lower()
            tokens.append(lemma)
        return " ".join(tokens)
    except Exception as e:
        logger.warning("SpaCy preprocessing failed, using regex fallback: %s", e)
        words = re.findall(r"\b[a-zA-Z0-9]+\b", text[:1000000])
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "to", "of", "in", "for", "on", "with", "at", "by", "from"}
        tokens = [w.lower() for w in words if w.lower() not in stop] if not preserve_case else [w for w in words if w.lower() not in stop]
        return " ".join(tokens)


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract named entities: organizations, dates, GPE (locations).
    Falls back to regex for dates if spaCy fails.
    """
    if not text or not text.strip():
        return {"ORG": [], "DATE": [], "GPE": [], "SKILL": []}
    result: dict[str, list[str]] = {"ORG": [], "DATE": [], "GPE": [], "SKILL": []}
    try:
        nlp = _get_nlp()
        doc = nlp(text[:500000])
        seen: dict[str, set[str]] = {k: set() for k in result}
        for ent in doc.ents:
            if ent.label_ in result and ent.text.strip():
                normalized = ent.text.strip()
                if normalized not in seen[ent.label_]:
                    seen[ent.label_].add(normalized)
                    result[ent.label_].append(normalized)
    except Exception as e:
        logger.warning("SpaCy NER failed, using regex fallback: %s", e)
        date_matches = re.findall(r"\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\b", text, re.I)
        result["DATE"] = list(dict.fromkeys(date_matches))
    return result


def get_noun_chunks(text: str) -> list[str]:
    """
    Extract noun chunks (phrases) from text. Falls back to empty list if spaCy fails.
    """
    if not text or not text.strip():
        return []
    try:
        nlp = _get_nlp()
        doc = nlp(text[:500000])
        chunks = [chunk.text.strip() for chunk in doc.noun_chunks if chunk.text.strip()]
        return list(dict.fromkeys(chunks))
    except Exception as e:
        logger.warning("SpaCy noun chunks failed: %s", e)
        return []
