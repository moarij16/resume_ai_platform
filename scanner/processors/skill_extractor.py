"""
Advanced skill detection using a taxonomy with synonyms and categories.

Supports context-aware extraction: section weights (Experience 3x, Skills 2x,
Education 1x), context tracking (role, company, dates), proficiency
signals, and estimated years per skill.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional

from ..config import (
    SKILLS_DB_PATH,
    MIN_SKILL_CONFIDENCE,
    SKILL_SECTION_WEIGHTS,
    SKILL_SECTION_WEIGHT_DEFAULT,
)
from ..utils.logger import get_logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MULTIWORD_SKILLS_PATH = DATA_DIR / "multiword_skills.json"

logger = get_logger(__name__)

_skills_db: Optional[dict[str, Any]] = None

# Proficiency phrases (before/after skill mention) -> level name
PROFICIENCY_PATTERNS = [
    (re.compile(r"\bexpert\s+(?:in|with|at)\s+", re.I), "expert"),
    (re.compile(r"\bexpert[- ]?level\s+", re.I), "expert"),
    (re.compile(r"\badvanced\s+(?:in|with|knowledge\s+of)\s+", re.I), "advanced"),
    (re.compile(r"\bproficient\s+(?:in|with)\s+", re.I), "proficient"),
    (re.compile(r"\bproficiency\s+in\s+", re.I), "proficient"),
    (re.compile(r"\bfamiliar\s+(?:with|in)\s+", re.I), "familiar"),
    (re.compile(r"\bfamiliarity\s+with\s+", re.I), "familiar"),
    (re.compile(r"\bbasic\s+(?:knowledge\s+of\s+)?", re.I), "basic"),
    (re.compile(r"\bworking\s+knowledge\s+of\s+", re.I), "intermediate"),
    (re.compile(r"\bextensive\s+experience\s+with\s+", re.I), "expert"),
    (re.compile(r"\bdeep\s+knowledge\s+of\s+", re.I), "expert"),
    (re.compile(r"\byears?\s+of\s+experience\s+with\s+", re.I), "experienced"),
]
# Suffix: "X expert", "X specialist"
PROFICIENCY_SUFFIX = re.compile(r"\b(expert|specialist|professional|advanced)\s*$", re.I)

# Date range in experience block for years attribution
DATE_RANGE = re.compile(
    r"(\d{4}|\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\s*[-–—to]+\s*"
    r"(present|current|now|\d{4}|\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.IGNORECASE,
)


def _load_skills_db() -> dict[str, Any]:
    """Load skills taxonomy once and cache."""
    global _skills_db
    if _skills_db is not None:
        return _skills_db
    path = Path(SKILLS_DB_PATH)
    if not path.exists():
        logger.warning("Skills taxonomy not found at %s; using empty taxonomy.", path)
        _skills_db = {}
        return _skills_db
    try:
        with open(path, encoding="utf-8") as f:
            _skills_db = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load skills taxonomy: %s", e)
        _skills_db = {}
    return _skills_db


def _build_skill_patterns(db: dict[str, Any]) -> list[tuple[str, str, str, float]]:
    """
    Build (pattern, canonical, category, weight) from taxonomy.
    Pattern is regex-ready; we match whole words.
    """
    patterns: list[tuple[str, str, str, float]] = []
    for category_key, skills in db.items():
        if not isinstance(skills, dict):
            continue
        for key, data in skills.items():
            if not isinstance(data, dict):
                continue
            canonical = data.get("canonical", key)
            variations = data.get("variations", [key])
            category = data.get("category", category_key)
            weight = float(data.get("weight", 1.0))
            for v in set(variations) | {key}:
                v = re.escape(v.strip())
                if not v:
                    continue
                pattern = r"\b" + v + r"\b"
                patterns.append((pattern, canonical, category, weight))
    return patterns


def _parse_date(s: str) -> int | None:
    """Return year as int or None."""
    if not s:
        return None
    s = s.strip().lower()
    if s in ("present", "current", "now"):
        from datetime import datetime
        return datetime.now().year
    try:
        import dateparser
        parsed = dateparser.parse(s)
        return parsed.year if parsed else None
    except Exception:
        pass
    match = re.search(r"\b(19|20)\d{2}\b", s)
    return int(match.group(0)) if match else None


def _split_experience_blocks(content: str) -> list[dict[str, Any]]:
    """
    Split experience section content into role blocks with title, company, dates, duration.
    Returns list of {role_title, company, start_year, end_year, duration_years, text}.
    """
    blocks: list[dict[str, Any]] = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = DATE_RANGE.search(line)
        if m:
            start_str, end_str = m.group(1), m.group(2)
            start_year = _parse_date(start_str)
            end_year = _parse_date(end_str)
            duration = None
            if start_year and end_year:
                duration = end_year - start_year + 1
                duration = min(max(0, duration), 50)
            # Title/company: previous non-empty line(s) or first line of block
            role_title = ""
            company = ""
            j = i - 1
            while j >= 0 and lines[j].strip():
                prev = lines[j].strip()
                if len(prev) < 80 and not re.match(r"^\d", prev):
                    role_title = prev
                    if j - 1 >= 0 and lines[j - 1].strip():
                        company = lines[j - 1].strip()[:80]
                    break
                j -= 1
            if not role_title:
                role_title = line[:m.start()].strip() or "Role"
            block_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not DATE_RANGE.search(lines[i]):
                block_lines.append(lines[i])
                i += 1
            block_text = "\n".join(block_lines)
            blocks.append({
                "role_title": role_title[:80],
                "company": company[:80],
                "start_year": start_year,
                "end_year": end_year,
                "duration_years": duration or 0,
                "text": block_text,
            })
            continue
        i += 1
    if not blocks:
        blocks.append({"role_title": "Experience", "company": "", "start_year": None, "end_year": None, "duration_years": 0, "text": content})
    return blocks


def _detect_proficiency_in_text(window: str) -> list[str]:
    """Detect proficiency signals in text window (e.g. around skill mention)."""
    found: list[str] = []
    for pattern, level in PROFICIENCY_PATTERNS:
        if pattern.search(window):
            found.append(level)
    if PROFICIENCY_SUFFIX.search(window):
        found.append("expert")
    return list(dict.fromkeys(found))


def normalize_skill(skill: str) -> str:
    """
    Convert skill variation to canonical form using taxonomy.

    Args:
        skill: Raw skill string (e.g. "reactjs", "React.js").

    Returns:
        Canonical form (e.g. "React") or original if not in taxonomy.
    """
    db = _load_skills_db()
    patterns = _build_skill_patterns(db)
    text_lower = skill.lower().strip()
    for pattern, canonical, _cat, _w in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return canonical
    return skill.strip()


def extract_skills(
    text: str,
    section_context: Optional[str] = None,
) -> dict[str, Any]:
    """
    Extract skills from text with context and confidence (simple, non–section-aware).

    Use for single-section or JD text. For full resume with section weights
    and per-skill details, use extract_skills_context_aware().

    Args:
        text: Resume or section text.
        section_context: Optional section name (e.g. "experience", "skills").

    Returns:
        Dictionary with detected_skills, skill_contexts, skill_categories, confidence_scores.
    """
    db = _load_skills_db()
    patterns = _build_skill_patterns(db)
    text_lower = text.lower()
    section_lower = (section_context or "").lower()
    is_experience = "experience" in section_lower or "employment" in section_lower
    is_skills_section = "skill" in section_lower

    detected: list[str] = []
    contexts: dict[str, list[str]] = {}
    categories: dict[str, list[str]] = {}
    confidence: dict[str, float] = {}

    for pattern, canonical, category, weight in patterns:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            snippet = text[m.start() : m.end() + 40].strip()
            if canonical not in detected:
                detected.append(canonical)
            contexts.setdefault(canonical, []).append(snippet[:80])
            categories.setdefault(category, [])
            if canonical not in categories[category]:
                categories[category].append(canonical)
            conf = min(1.0, weight)
            if is_experience:
                conf = min(1.0, conf * 1.2)
            if is_skills_section:
                conf = min(1.0, conf * 1.1)
            if canonical not in confidence or conf > confidence[canonical]:
                confidence[canonical] = conf

    min_conf = MIN_SKILL_CONFIDENCE
    detected = [s for s in detected if confidence.get(s, 0) >= min_conf]
    for k in list(contexts.keys()):
        if k not in detected:
            del contexts[k]
            if k in confidence:
                del confidence[k]
    for cat in categories:
        categories[cat] = [s for s in categories[cat] if s in detected]

    return {
        "detected_skills": detected,
        "skill_contexts": contexts,
        "skill_categories": categories,
        "confidence_scores": confidence,
    }


def extract_skills_context_aware(resume_text: str) -> dict[str, Any]:
    """
    Extract skills with section weighting, context, proficiency signals, and estimated years.

    Weights: Experience 3x, Skills 2x, Education 1x. Tracks where each skill appears
    (job title, company, project), detects proficiency language, and estimates years
    per skill from date ranges in the experience section.

    Args:
        resume_text: Full resume text (section headers will be detected).

    Returns:
        Dictionary with:
          skills: dict[skill_name, {mentions, contexts, estimated_years,
                  proficiency_signals, weighted_score}]
          detected_skills: list of skill names (for backward compatibility)
          skill_categories: category -> list of skills
    """
    from ..analyzers.section_detector import detect_sections

    db = _load_skills_db()
    patterns = _build_skill_patterns(db)
    sections_result = detect_sections(resume_text)
    sections = sections_result.get("sections", [])

    # Aggregate per skill: mentions, contexts, years, proficiency, weighted contribution
    skill_data: dict[str, dict[str, Any]] = {}
    categories: dict[str, list[str]] = {}

    for section in sections:
        name = (section.get("name") or "").strip().lower()
        content = section.get("content") or ""
        section_weight = SKILL_SECTION_WEIGHTS.get(name, SKILL_SECTION_WEIGHT_DEFAULT)
        is_experience = "experience" in name or "employment" in name

        if is_experience:
            blocks = _split_experience_blocks(content)
            for block in blocks:
                role_title = block.get("role_title") or "Role"
                company = block.get("company") or ""
                duration = block.get("duration_years") or 0
                block_text = block.get("text") or ""
                context_label = role_title
                if company:
                    context_label = f"{role_title} at {company}"
                _extract_skills_in_text(
                    block_text,
                    patterns,
                    section_weight,
                    skill_data,
                    categories,
                    context_label=context_label,
                    years_for_block=duration,
                )
        else:
            context_label = name.replace(" ", " ").title()
            _extract_skills_in_text(
                content,
                patterns,
                section_weight,
                skill_data,
                categories,
                context_label=context_label,
                years_for_block=0,
            )
        _extract_multiword_and_certifications(
            content,
            section_weight,
            skill_data,
            categories,
            context_label=context_label or name.replace(" ", " ").title(),
        )

    # Build final per-skill structure and weighted_score
    result_skills: dict[str, dict[str, Any]] = {}
    for canonical, data in skill_data.items():
        if data.get("weighted_sum", 0) < MIN_SKILL_CONFIDENCE:
            continue
        mentions = data.get("mentions", 0)
        contexts_list = list(dict.fromkeys(data.get("contexts", [])))[:10]
        estimated_years = data.get("estimated_years", 0)
        proficiency_signals = list(dict.fromkeys(data.get("proficiency_signals", [])))
        # weighted_score: combine section-weighted mentions + years + proficiency
        weighted_sum = data.get("weighted_sum", 0)
        years_component = min(10, estimated_years) * 0.5
        prof_component = len(proficiency_signals) * 0.5 if proficiency_signals else 0
        weighted_score = round(weighted_sum + years_component + prof_component, 1)
        result_skills[canonical] = {
            "mentions": mentions,
            "contexts": contexts_list,
            "estimated_years": estimated_years,
            "proficiency_signals": proficiency_signals,
            "weighted_score": weighted_score,
        }

    detected = list(result_skills.keys())
    skill_categories = _build_categories_from_skills(result_skills, db)
    for cat, skill_list in categories.items():
        for s in skill_list:
            if s in result_skills and s not in skill_categories.get(cat, []):
                skill_categories.setdefault(cat, []).append(s)

    return {
        "skills": result_skills,
        "detected_skills": detected,
        "skill_categories": skill_categories,
    }


def _extract_skills_in_text(
    text: str,
    patterns: list[tuple[str, str, str, float]],
    section_weight: float,
    skill_data: dict[str, dict[str, Any]],
    categories: dict[str, list[str]],
    *,
    context_label: str = "",
    years_for_block: int = 0,
) -> None:
    """Find skills in text, update skill_data with mentions, context, years, proficiency."""
    text_lower = text.lower()
    skills_given_years_this_block: set[str] = set()
    for pattern, canonical, category, base_weight in patterns:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            start, end = m.start(), m.end()
            window_before = text[max(0, start - 60) : start]
            window_after = text[end : min(len(text), end + 60)]
            window = window_before + " " + window_after
            proficiency = _detect_proficiency_in_text(window)
            if canonical not in skill_data:
                skill_data[canonical] = {
                    "mentions": 0,
                    "contexts": [],
                    "estimated_years": 0,
                    "proficiency_signals": [],
                    "weighted_sum": 0.0,
                }
                if canonical not in categories.get(category, []):
                    categories.setdefault(category, []).append(canonical)
            skill_data[canonical]["mentions"] += 1
            if context_label and context_label not in skill_data[canonical]["contexts"]:
                skill_data[canonical]["contexts"].append(context_label)
            if years_for_block > 0 and canonical not in skills_given_years_this_block:
                skills_given_years_this_block.add(canonical)
                skill_data[canonical]["estimated_years"] = (
                    skill_data[canonical].get("estimated_years", 0) + years_for_block
                )
            skill_data[canonical]["proficiency_signals"] = list(
                dict.fromkeys(
                    skill_data[canonical].get("proficiency_signals", []) + proficiency
                )
            )
            contribution = base_weight * section_weight
            skill_data[canonical]["weighted_sum"] = (
                skill_data[canonical].get("weighted_sum", 0) + contribution
            )


def _load_multiword_data() -> dict[str, Any]:
    """Load multi-word phrases and tech stacks."""
    if not MULTIWORD_SKILLS_PATH.exists():
        return {"phrases": [], "phrase_canonical": {}, "tech_stacks": {}, "certification_patterns": []}
    try:
        with open(MULTIWORD_SKILLS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load multiword skills: %s", e)
        return {"phrases": [], "phrase_canonical": {}, "tech_stacks": {}, "certification_patterns": []}


def _extract_multiword_and_certifications(
    text: str,
    section_weight: float,
    skill_data: dict[str, dict[str, Any]],
    categories: dict[str, list[str]],
    *,
    context_label: str = "",
) -> None:
    """Extract multi-word skills (Machine Learning, React Native), tech stacks (MERN), and certifications."""
    data = _load_multiword_data()
    text_lower = text.lower()
    phrase_canonical = data.get("phrase_canonical") or {}
    for phrase_str, canonical in phrase_canonical.items():
        pattern = r"\b" + re.escape(phrase_str) + r"\b"
        if re.search(pattern, text_lower, re.IGNORECASE):
            if canonical not in skill_data:
                skill_data[canonical] = {
                    "mentions": 0,
                    "contexts": [],
                    "estimated_years": 0,
                    "proficiency_signals": [],
                    "weighted_sum": 0.0,
                }
                categories.setdefault("Multi-word / Phrase", []).append(canonical)
            skill_data[canonical]["mentions"] += 1
            if context_label and context_label not in skill_data[canonical]["contexts"]:
                skill_data[canonical]["contexts"].append(context_label)
            skill_data[canonical]["weighted_sum"] = (
                skill_data[canonical].get("weighted_sum", 0) + 1.0 * section_weight
            )
    for stack_name, skills in (data.get("tech_stacks") or {}).items():
        if re.search(r"\b" + re.escape(stack_name) + r"\b", text_lower):
            for sk in skills:
                if sk not in skill_data:
                    skill_data[sk] = {
                        "mentions": 0,
                        "contexts": [],
                        "estimated_years": 0,
                        "proficiency_signals": [],
                        "weighted_sum": 0.0,
                    }
                    categories.setdefault("Tech Stack", []).append(sk)
                skill_data[sk]["mentions"] += 1
                if context_label and context_label not in skill_data[sk]["contexts"]:
                    skill_data[sk]["contexts"].append(f"{stack_name} stack")
                skill_data[sk]["weighted_sum"] = (
                    skill_data[sk].get("weighted_sum", 0) + 0.9 * section_weight
                )
    for cert in (data.get("certification_patterns") or []):
        if cert.lower() in text_lower:
            if cert not in skill_data:
                skill_data[cert] = {
                    "mentions": 0,
                    "contexts": [],
                    "estimated_years": 0,
                    "proficiency_signals": [],
                    "weighted_sum": 0.0,
                }
                categories.setdefault("Certification", []).append(cert)
            skill_data[cert]["mentions"] += 1
            if context_label and context_label not in skill_data[cert]["contexts"]:
                skill_data[cert]["contexts"].append(context_label)
            skill_data[cert]["weighted_sum"] = (
                skill_data[cert].get("weighted_sum", 0) + 1.0 * section_weight
            )


def _build_categories_from_skills(
    result_skills: dict[str, dict[str, Any]],
    db: dict[str, Any],
) -> dict[str, list[str]]:
    """Map each skill back to its category from taxonomy."""
    canonical_to_category: dict[str, str] = {}
    for category_key, skills in db.items():
        if not isinstance(skills, dict):
            continue
        for key, data in skills.items():
            if not isinstance(data, dict):
                continue
            canonical = data.get("canonical", key)
            cat = data.get("category", category_key)
            canonical_to_category[canonical] = cat
    out: dict[str, list[str]] = {}
    for skill_name in result_skills:
        cat = canonical_to_category.get(skill_name, "Other")
        out.setdefault(cat, []).append(skill_name)
    return out
