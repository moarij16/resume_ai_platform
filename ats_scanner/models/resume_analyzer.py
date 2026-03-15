"""
Standalone resume quality analysis (Mode 2): no job description.
"""

from typing import Any

from ..config import (
    WEIGHT_SECTION_COMPLETENESS,
    WEIGHT_KEYWORD_STRENGTH,
    WEIGHT_BULLET_QUALITY,
    WEIGHT_FORMAT_COMPATIBILITY,
    WEIGHT_CONTENT_QUANTIFICATION,
    WEIGHT_RESUME_LENGTH,
    REQUIRED_SECTIONS,
    OPTIMAL_WORD_COUNT,
    PENALTY_TOO_SHORT_THRESHOLD,
)
from ..analyzers.section_detector import detect_sections
from ..analyzers.format_checker import check_format
from ..analyzers.content_analyzer import analyze_bullets
from ..processors.skill_extractor import extract_skills_context_aware
from ..utils.logger import get_logger

logger = get_logger(__name__)


def analyze_resume_quality(
    resume_text: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compute resume quality score and report when no JD is provided.

    Args:
        resume_text: Full resume text.
        metadata: Optional parser metadata for format checks.

    Returns:
        Dictionary with quality_score (0-100), section_completeness,
        keyword_strength, bullet_quality, format_compatibility,
        content_quantification, resume_length, and recommendations.
    """
    meta = metadata or {}
    sections_result = detect_sections(resume_text)
    format_warnings = check_format(resume_text, meta)
    bullets = analyze_bullets(resume_text)
    skills_data = extract_skills_context_aware(resume_text)
    detected_skills = skills_data.get("detected_skills", [])

    # Section completeness: required (summary, experience, education, skills) + optional
    section_names = set(sections_result.get("section_names", []))
    required_core = {"professional summary", "summary", "objective", "work experience", "education", "skills"}
    required_found = sum(1 for s in required_core if s in section_names)
    required_total = 4  # Expect at least 4 of: summary/objective, experience, education, skills
    optional_found = len([s for s in section_names if s not in required_core])
    section_completeness = (required_found / required_total) * 0.7 + min(1.0, optional_found / 6) * 0.3
    section_completeness = min(1.0, section_completeness)

    # Keyword strength: diversity and count
    skill_count = len(detected_skills)
    keyword_strength = min(1.0, skill_count / 25.0) * 0.6 + min(1.0, len(resume_text) / 2000) * 0.4

    # Bullet quality
    total_b = bullets.get("total_bullets", 0) or 1
    with_verbs = bullets.get("bullets_with_action_verbs", 0)
    with_metrics = bullets.get("bullets_with_metrics", 0)
    bullet_quality = (with_verbs / total_b) * 0.5 + (with_metrics / total_b) * 0.5

    # Format compatibility: penalize warnings
    high = sum(1 for w in format_warnings if w.get("severity") == "high")
    medium = sum(1 for w in format_warnings if w.get("severity") == "medium")
    format_compatibility = max(0.0, 1.0 - high * 0.2 - medium * 0.1)

    # Content quantification
    metrics_ratio = with_metrics / total_b if total_b else 0
    content_quantification = min(1.0, metrics_ratio / 0.7)

    # Resume length
    word_count = len(resume_text.split())
    if word_count < PENALTY_TOO_SHORT_THRESHOLD:
        length_score = word_count / PENALTY_TOO_SHORT_THRESHOLD
    elif OPTIMAL_WORD_COUNT[0] <= word_count <= OPTIMAL_WORD_COUNT[1]:
        length_score = 1.0
    elif word_count <= 1200:
        length_score = 0.9
    else:
        length_score = max(0.5, 1.0 - (word_count - 1200) / 2000)

    quality_score = (
        WEIGHT_SECTION_COMPLETENESS * section_completeness
        + WEIGHT_KEYWORD_STRENGTH * keyword_strength
        + WEIGHT_BULLET_QUALITY * bullet_quality
        + WEIGHT_FORMAT_COMPATIBILITY * format_compatibility
        + WEIGHT_CONTENT_QUANTIFICATION * content_quantification
        + WEIGHT_RESUME_LENGTH * length_score
    )
    quality_score = round(min(100.0, max(0.0, quality_score * 100)), 1)

    recommendations = []
    if section_completeness < 0.8:
        recommendations.append("Add missing sections (e.g. Summary, Experience, Education, Skills).")
    if bullet_quality < 0.6:
        recommendations.append("Start bullets with action verbs and add metrics where possible.")
    if format_compatibility < 0.9:
        recommendations.append("Use ATS-friendly formatting: avoid tables and images.")
    if content_quantification < 0.6:
        recommendations.append("Increase quantified achievements (numbers, percentages, scale).")
    if length_score < 0.8 and word_count < PENALTY_TOO_SHORT_THRESHOLD:
        recommendations.append("Expand resume to at least 300 words with concrete details.")
    if not detected_skills:
        recommendations.append("Add a clear Skills section with relevant keywords.")

    return {
        "quality_score": quality_score,
        "section_completeness": round(section_completeness * 100, 1),
        "keyword_strength": round(keyword_strength * 100, 1),
        "bullet_quality": round(bullet_quality * 100, 1),
        "format_compatibility": round(format_compatibility * 100, 1),
        "content_quantification": round(content_quantification * 100, 1),
        "resume_length_score": round(length_score * 100, 1),
        "word_count": word_count,
        "sections": sections_result,
        "format_warnings": format_warnings,
        "bullets": bullets,
        "detected_skills": detected_skills,
        "skills_detail": skills_data.get("skills", {}),
        "recommendations": recommendations[:6],
    }
