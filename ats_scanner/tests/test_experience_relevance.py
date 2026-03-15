"""Tests for experience relevance scoring."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))


def test_experience_relevance_structure():
    from ats_scanner.engines.experience_relevance import score_experience_relevance
    jobs = [
        {"title": "Software Engineer", "company": "Acme", "start_year": 2020, "end_year": 2023, "duration_years": 3},
    ]
    out = score_experience_relevance(jobs, "We need a Software Engineer.", jd_title="Software Engineer")
    assert "combined_score" in out
    assert "title_match" in out
    assert "recency_weight" in out
    assert "progression_score" in out
    assert 0 <= out["combined_score"] <= 1


def test_experience_relevance_empty_jobs():
    from ats_scanner.engines.experience_relevance import score_experience_relevance
    out = score_experience_relevance([], "JD text")
    assert out["combined_score"] == 0.0
