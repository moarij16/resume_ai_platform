"""
ATS compatibility scorer: Resume vs Job Description (Mode 1).
Uses multi-tier skill matching, experience relevance, section-weighted scoring,
keyword density, and actionable recommendations.
"""

from typing import Any

from ..config import (
    WEIGHT_SKILL_MATCH,
    WEIGHT_KEYWORD_SIMILARITY,
    WEIGHT_SEMANTIC_SIMILARITY,
    WEIGHT_EXPERIENCE_RELEVANCE,
    SECTION_WEIGHTS_SCORING,
    SECTION_WEIGHT_SCORING_DEFAULT,
)
from ..processors.skill_extractor import extract_skills, extract_skills_context_aware
from ..analyzers.section_detector import detect_sections
from ..analyzers.experience_parser import parse_experience
from ..analyzers.content_analyzer import analyze_bullets
from .similarity_engine import (
    compute_tfidf_similarity,
    compute_semantic_similarity,
)
from .skill_similarity import calculate_skill_similarity
from .experience_relevance import score_experience_relevance
from .keyword_density import compute_keyword_density
from .recommendations import build_actionable_recommendations
from ..utils.logger import get_logger

logger = get_logger(__name__)


def score_resume_vs_jd(
    resume_text: str,
    job_description: str,
) -> dict[str, Any]:
    """
    Compute ATS score and breakdown when job description is provided.

    Args:
        resume_text: Full resume text.
        job_description: Job description text.

    Returns:
        Dictionary with ats_score (0-100), breakdown, matched_skills,
        missing_critical_skills, matched_keywords, recommendations.
    """
    # Skills: multi-tier matching (exact, synonym, related via embeddings)
    jd_skills_data = extract_skills(job_description)
    jd_skills_list = jd_skills_data.get("detected_skills", [])
    jd_skills = set(s.lower() for s in jd_skills_list)
    resume_skills_data = extract_skills_context_aware(resume_text)
    resume_skills_list = resume_skills_data.get("detected_skills", [])
    resume_skills_set = set(s.lower() for s in resume_skills_list)
    matched_skills = list(resume_skills_set & jd_skills)
    missing = list(jd_skills - resume_skills_set)
    # Multi-tier: for each JD skill, best similarity to any resume skill
    tier_scores = []
    for jd_sk in jd_skills_list:
        best = 0.0
        for res_sk in resume_skills_list:
            sim = calculate_skill_similarity(res_sk, jd_sk)
            if sim > best:
                best = sim
        tier_scores.append(best)
    skill_match = sum(tier_scores) / len(tier_scores) if tier_scores else (1.0 if not jd_skills else 0.0)

    # Keyword (TF-IDF) and semantic similarity
    try:
        keyword_sim = compute_tfidf_similarity(resume_text, job_description)
    except Exception:
        keyword_sim = 0.0
    try:
        semantic_sim = compute_semantic_similarity(resume_text, job_description)
    except Exception:
        semantic_sim = 0.0

    # Experience relevance: title match, recency, career progression
    exp_data = parse_experience(resume_text)
    total_years = exp_data.get("total_years", 0)
    jobs = exp_data.get("experiences", [])
    exp_relevance = score_experience_relevance(jobs, job_description)
    experience_relevance = exp_relevance.get("combined_score", 0.5) * 0.6 + 0.4 * min(1.0, total_years / 10.0)

    ats_score = (
        WEIGHT_SKILL_MATCH * skill_match
        + WEIGHT_KEYWORD_SIMILARITY * keyword_sim
        + WEIGHT_SEMANTIC_SIMILARITY * semantic_sim
        + WEIGHT_EXPERIENCE_RELEVANCE * experience_relevance
    )
    ats_score = round(min(100.0, max(0.0, ats_score * 100)), 1)

    # Matched keywords (count in resume)
    from collections import Counter
    jd_words = set(job_description.lower().split())
    resume_words = resume_text.lower().split()
    matched_keywords = dict(Counter(w for w in resume_words if w in jd_words and len(w) > 2))
    matched_keywords = dict(sorted(matched_keywords.items(), key=lambda x: -x[1])[:30])

    # Keyword density and actionable recommendations
    critical_kw = list(jd_skills_list)[:15] + job_description.lower().split()[:20]
    critical_kw = list(dict.fromkeys(k for k in critical_kw if len(k) > 2))[:15]
    keyword_density = compute_keyword_density(resume_text, critical_kw, SECTION_WEIGHTS_SCORING)
    bullets = analyze_bullets(resume_text)
    actionable = build_actionable_recommendations(
        missing_skills=[s for s in missing[:10]],
        weak_bullets=bullets.get("weak_bullets"),
        keyword_density=keyword_density,
        jd_keywords=jd_skills_list,
    )
    legacy_recs = []
    if missing:
        legacy_recs.append(f"Add missing skills: {', '.join(missing[:5])}.")
    if keyword_sim < 0.5:
        legacy_recs.append("Align resume language with job description keywords.")

    return {
        "ats_score": ats_score,
        "breakdown": {
            "skill_match": round(skill_match * 100, 1),
            "keyword_similarity": round(keyword_sim * 100, 1),
            "semantic_similarity": round(semantic_sim * 100, 1),
            "experience_relevance": round(experience_relevance * 100, 1),
        },
        "experience_relevance_detail": exp_relevance,
        "matched_skills": matched_skills,
        "missing_critical_skills": missing[:15],
        "matched_keywords": matched_keywords,
        "recommendations": legacy_recs[:5],
        "actionable_recommendations": actionable,
        "keyword_density": keyword_density,
        "skills_detail": resume_skills_data.get("skills", {}),
    }
