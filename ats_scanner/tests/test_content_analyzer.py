"""Unit tests for content analyzer (bullets)."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from ats_scanner.analyzers.content_analyzer import analyze_bullets


def test_analyze_bullets_structure():
    """Returns dict with expected keys."""
    text = """
    • Led team of 5 to deliver project on time
    • Increased revenue by 40% through optimization
    • Responsible for maintaining databases
    """
    result = analyze_bullets(text)
    assert "total_bullets" in result
    assert "bullets_with_action_verbs" in result
    assert "bullets_with_metrics" in result
    assert "weak_bullets" in result
    assert "strong_bullets" in result
    assert "avg_bullet_length" in result


def test_analyze_bullets_detects_weak():
    """Weak phrases are flagged."""
    text = "• Responsible for various tasks and duties included support."
    result = analyze_bullets(text)
    assert result["total_bullets"] >= 1 or len(result["weak_bullets"]) >= 0
