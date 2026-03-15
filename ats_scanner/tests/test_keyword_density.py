"""Tests for keyword density engine."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))


def test_keyword_density_structure():
    from ats_scanner.engines.keyword_density import compute_keyword_density
    text = "Python is great. I use Python every day. Python and Java."
    result = compute_keyword_density(text, ["Python", "Java"])
    assert "Python" in result
    assert result["Python"]["mention_count"] >= 3
    assert "current_density_pct" in result["Python"]
    assert "safe_locations" in result["Python"]


def test_keyword_density_empty_keywords():
    from ats_scanner.engines.keyword_density import compute_keyword_density
    assert compute_keyword_density("Some text", []) == {}
