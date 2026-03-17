"""
Configuration and constants for the ATS Resume Scanner.

This module centralizes all configurable parameters, file paths,
and model names used across the scanner pipeline.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to ats_scanner package root)
# ---------------------------------------------------------------------------
PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"

SKILLS_DB_PATH = DATA_DIR / "skills_taxonomy.json"
ACTION_VERBS_PATH = DATA_DIR / "action_verbs.json"
ATS_KEYWORDS_PATH = DATA_DIR / "ats_keywords.json"

# ---------------------------------------------------------------------------
# NLP Models
# ---------------------------------------------------------------------------
SPACY_MODEL = "en_core_web_md"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Skill Extraction
# ---------------------------------------------------------------------------
MIN_SKILL_CONFIDENCE = 0.6
EXPERIENCE_SECTION_WEIGHT = 1.2  # Weight skills mentioned in experience higher
SKILLS_SECTION_WEIGHT = 1.0

# Context-aware skill extraction: weight by section
SKILL_SECTION_WEIGHTS = {
    "work experience": 3.0,
    "professional experience": 3.0,
    "employment": 3.0,
    "experience": 3.0,
    "skills": 2.0,
    "technical skills": 2.0,
    "education": 1.0,
}
SKILL_SECTION_WEIGHT_DEFAULT = 1.0

# ---------------------------------------------------------------------------
# Resume Length & Format
# ---------------------------------------------------------------------------
MAX_RESUME_LENGTH_PAGES = 3
MIN_RESUME_WORDS = 300
OPTIMAL_WORD_COUNT = (400, 800)  # (min, max) for "optimal" length score
PENALTY_TOO_SHORT_THRESHOLD = 300
PENALTY_TOO_LONG_WORDS = 1200  # ~3 pages at ~400 words/page

# ---------------------------------------------------------------------------
# ATS Scoring Weights (Mode 1: Resume vs JD)
# ---------------------------------------------------------------------------
WEIGHT_SKILL_MATCH = 0.40
WEIGHT_KEYWORD_SIMILARITY = 0.25
WEIGHT_SEMANTIC_SIMILARITY = 0.25
WEIGHT_EXPERIENCE_RELEVANCE = 0.10

# ---------------------------------------------------------------------------
# Quality Score Weights (Mode 2: Standalone)
# ---------------------------------------------------------------------------
WEIGHT_SECTION_COMPLETENESS = 0.20
WEIGHT_KEYWORD_STRENGTH = 0.20
WEIGHT_BULLET_QUALITY = 0.20
WEIGHT_FORMAT_COMPATIBILITY = 0.15
WEIGHT_CONTENT_QUANTIFICATION = 0.15
WEIGHT_RESUME_LENGTH = 0.10

# ---------------------------------------------------------------------------
# Similarity Engine
# ---------------------------------------------------------------------------
DEFAULT_TFIDF_WEIGHT = 0.4
DEFAULT_SEMANTIC_WEIGHT = 0.6

# ---------------------------------------------------------------------------
# Content Analysis
# ---------------------------------------------------------------------------
MIN_BULLET_LENGTH_WORDS = 5
MAX_BULLET_LENGTH_WORDS = 35
TARGET_METRICS_PER_BULLET = 0.7
WEAK_PHRASE_PENALTY = 0.2

# ---------------------------------------------------------------------------
# Section Names (for detection)
# ---------------------------------------------------------------------------
REQUIRED_SECTIONS = [
    "professional summary",
    "summary",
    "objective",
    "work experience",
    "employment",
    "experience",
    "education",
    "skills",
    "technical skills",
]
OPTIONAL_SECTIONS = [
    "projects",
    "certifications",
    "licenses",
    "awards",
    "achievements",
    "publications",
    "volunteer",
    "languages",
]

# ---------------------------------------------------------------------------
# Section weights for scoring (context: experience > projects > skills > education)
# ---------------------------------------------------------------------------
SECTION_WEIGHTS_SCORING = {
    "work experience": 1.0,
    "professional experience": 1.0,
    "employment": 1.0,
    "experience": 1.0,
    "projects": 0.9,
    "skills": 0.6,
    "technical skills": 0.6,
    "education": 0.5,
}
SECTION_WEIGHT_SCORING_DEFAULT = 0.7

# ---------------------------------------------------------------------------
# Keyword density (optimal 2–3%, flag over-stuffing above max)
# ---------------------------------------------------------------------------
OPTIMAL_KEYWORD_DENSITY_PCT = 2.5
KEYWORD_DENSITY_MIN_PCT = 1.0
KEYWORD_DENSITY_MAX_PCT = 5.0

# ---------------------------------------------------------------------------
# Severity & thresholds
# ---------------------------------------------------------------------------
MIN_ATS_SCORE = 70
CRITICAL_SKILL_MATCH_RATIO = 0.80
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
ATS_PROFILES_PATH = DATA_DIR / "ats_profiles.json"
SYNONYMS_PATH = DATA_DIR / "synonyms_acronyms.json"

# ---------------------------------------------------------------------------
# Optional YAML overlay (if PyYAML and config.yaml present)
# ---------------------------------------------------------------------------
def _load_yaml_config() -> None:
    """Override module defaults from config.yaml if present."""
    yaml_path = PACKAGE_ROOT / "config.yaml"
    if not yaml_path.exists():
        return
    try:
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return
        glob = globals()
        if "models" in data:
            if "spacy" in data["models"]:
                glob["SPACY_MODEL"] = data["models"]["spacy"]
            if "sentence_transformer" in data["models"]:
                glob["EMBEDDING_MODEL"] = data["models"]["sentence_transformer"]
        if "scoring" in data:
            s = data["scoring"]
            if "skill_weight" in s:
                glob["WEIGHT_SKILL_MATCH"] = float(s["skill_weight"])
            if "keyword_weight" in s:
                glob["WEIGHT_KEYWORD_SIMILARITY"] = float(s["keyword_weight"])
            if "semantic_weight" in s:
                glob["WEIGHT_SEMANTIC_SIMILARITY"] = float(s["semantic_weight"])
            if "experience_weight" in s:
                glob["WEIGHT_EXPERIENCE_RELEVANCE"] = float(s["experience_weight"])
        if "thresholds" in data:
            t = data["thresholds"]
            if "min_ats_score" in t:
                glob["MIN_ATS_SCORE"] = int(t["min_ats_score"])
            if "optimal_keyword_density_pct" in t:
                glob["OPTIMAL_KEYWORD_DENSITY_PCT"] = float(t["optimal_keyword_density_pct"])
            if "keyword_density_max_pct" in t:
                glob["KEYWORD_DENSITY_MAX_PCT"] = float(t["keyword_density_max_pct"])
        if "section_weights_scoring" in data:
            glob["SECTION_WEIGHTS_SCORING"] = {k: float(v) for k, v in data["section_weights_scoring"].items()}
    except Exception:
        pass


_load_yaml_config()
