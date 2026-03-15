"""Unit tests for skill extractor."""

import sys
from pathlib import Path

# Add repo root for imports
root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import pytest
from ats_scanner.processors.skill_extractor import normalize_skill, extract_skills


def test_normalize_skill_known():
    """Canonical form returned for known skill variations."""
    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("AWS") == "AWS"


def test_normalize_skill_unknown():
    """Unknown skill returned as-is (trimmed)."""
    assert normalize_skill("  UnknownSkill  ") == "UnknownSkill"


def test_extract_skills_returns_structure():
    """extract_skills returns dict with required keys."""
    text = "I used Python and JavaScript to build React applications with Docker."
    result = extract_skills(text)
    assert "detected_skills" in result
    assert "skill_contexts" in result
    assert "skill_categories" in result
    assert "confidence_scores" in result
    assert isinstance(result["detected_skills"], list)


def test_extract_skills_detects_skills():
    """Common skills are detected in text."""
    text = "Experience with Python, SQL, and AWS. Used Docker and Kubernetes."
    result = extract_skills(text)
    skills = [s.lower() for s in result["detected_skills"]]
    assert "python" in skills or "sql" in skills or "aws" in skills
