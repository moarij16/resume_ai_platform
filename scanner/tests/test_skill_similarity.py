"""Tests for multi-tier skill similarity."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))


def test_skill_similarity_exact():
    from scanner.scorers.skill_similarity import calculate_skill_similarity
    assert calculate_skill_similarity("Python", "Python") == 1.0
    assert calculate_skill_similarity("python", "Python") == 1.0


def test_skill_similarity_returns_float():
    from scanner.scorers.skill_similarity import calculate_skill_similarity
    s = calculate_skill_similarity("React", "Vue")
    assert isinstance(s, (int, float))
    assert 0 <= s <= 1
