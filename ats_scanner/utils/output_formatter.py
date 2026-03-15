"""
Multi-format output: text (terminal), JSON, HTML.
"""

import json
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


def format_output(
    result: dict[str, Any],
    mode: str,
    output_path: str | None = None,
) -> str:
    """
    Format analysis result as text, JSON, or HTML.

    Args:
        result: Mode 1 (ats_result) or Mode 2 (quality_result) dict.
        mode: One of "text", "json", "html".
        output_path: If set, write output to this file.

    Returns:
        Formatted string (and optionally writes to file).
    """
    if mode == "json":
        out = json.dumps(result, indent=2, default=str)
    elif mode == "html":
        out = _format_html(result)
    else:
        out = _format_text(result)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(out)
    return out


def _format_text(result: dict[str, Any]) -> str:
    """Plain text with box-drawing and sections."""
    if "ats_score" in result:
        return _text_mode1(result)
    return _text_mode2(result)


def _text_mode1(r: dict[str, Any]) -> str:
    """Format ATS compatibility result (Mode 1)."""
    lines = [
        "╔═══════════════════════════════════════╗",
        "║     ATS COMPATIBILITY ANALYSIS       ║",
        "╚═══════════════════════════════════════╝",
        "",
        f"📊 OVERALL ATS SCORE: {r.get('ats_score', 0)}% (Good Match)" if r.get("ats_score", 0) >= 60 else f"📊 OVERALL ATS SCORE: {r.get('ats_score', 0)}%",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📈 SCORE BREAKDOWN:",
    ]
    br = r.get("breakdown", {})
    for k, v in br.items():
        label = k.replace("_", " ").title()
        lines.append(f"  ✓ {label}: {v}%")
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"✅ MATCHED SKILLS ({len(r.get('matched_skills', []))}):",
    ])
    for s in (r.get("matched_skills") or [])[:20]:
        lines.append(f"  • {s}")
    miss = r.get("missing_critical_skills") or []
    if miss:
        lines.extend(["", f"❌ MISSING CRITICAL SKILLS ({len(miss)}):"])
        for s in miss[:10]:
            lines.append(f"  • {s}")
    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "💡 ACTIONABLE RECOMMENDATIONS:"])
    for i, rec in enumerate(r.get("actionable_recommendations") or r.get("recommendations") or [], 1):
        if isinstance(rec, dict):
            lines.append(f"  [{rec.get('severity', '')}] {rec.get('title', '')}")
            for a in rec.get("actions", [])[:3]:
                lines.append(f"    → {a}")
            if rec.get("estimated_impact_pct"):
                lines.append(f"    📈 Est. impact: +{rec['estimated_impact_pct']}%")
        else:
            lines.append(f"  {i}. {rec}")
    for rec in r.get("recommendations") or []:
        if rec and not r.get("actionable_recommendations"):
            lines.append(f"  • {rec}")
    return "\n".join(lines)


def _text_mode2(r: dict[str, Any]) -> str:
    """Format quality analysis result (Mode 2)."""
    lines = [
        "╔═══════════════════════════════════════╗",
        "║     RESUME QUALITY ANALYSIS          ║",
        "╚═══════════════════════════════════════╝",
        "",
        f"📊 OVERALL QUALITY SCORE: {r.get('quality_score', 0)}%",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📋 SECTION COMPLETENESS: {r.get('section_completeness', 0)}%",
        f"🎯 KEYWORD STRENGTH: {r.get('keyword_strength', 0)}%",
        f"📝 BULLET POINT QUALITY: {r.get('bullet_quality', 0)}%",
        f"✅ ATS FORMAT COMPATIBILITY: {r.get('format_compatibility', 0)}%",
        f"📊 CONTENT QUANTIFICATION: {r.get('content_quantification', 0)}%",
        f"📄 RESUME LENGTH: {r.get('resume_length_score', 0)}% (words: {r.get('word_count', 0)})",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 TOP RECOMMENDATIONS:",
    ]
    for i, rec in enumerate((r.get("recommendations") or []), 1):
        lines.append(f"  {i}. {rec}")
    return "\n".join(lines)


def _format_html(result: dict[str, Any]) -> str:
    """Simple HTML report."""
    if "ats_score" in result:
        return _html_mode1(result)
    return _html_mode2(result)


def _html_mode1(r: dict[str, Any]) -> str:
    title = "ATS Compatibility Analysis"
    score = r.get("ats_score", 0)
    body = f"<h1>{title}</h1><p><strong>ATS Score: {score}%</strong></p><h2>Breakdown</h2><ul>"
    for k, v in (r.get("breakdown") or {}).items():
        body += f"<li>{k}: {v}%</li>"
    body += "</ul><h2>Matched Skills</h2><ul>"
    for s in r.get("matched_skills") or []:
        body += f"<li>{s}</li>"
    body += "</ul><h2>Actionable Recommendations</h2>"
    for rec in r.get("actionable_recommendations") or []:
        if isinstance(rec, dict):
            body += f"<div style='margin:10px 0;padding:8px;border-left:4px solid #333'><strong>[{rec.get('severity')}]</strong> {rec.get('title')}<ul>"
            for a in rec.get("actions", []):
                body += f"<li>{a}</li>"
            if rec.get("estimated_impact_pct"):
                body += f"<li>Est. impact: +{rec['estimated_impact_pct']}%</li>"
            body += "</ul></div>"
    body += "<h2>Recommendations</h2><ul>"
    for rec in r.get("recommendations") or []:
        body += f"<li>{rec}</li>"
    body += "</ul>"
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title></head><body>{body}</body></html>"


def _html_mode2(r: dict[str, Any]) -> str:
    title = "Resume Quality Analysis"
    score = r.get("quality_score", 0)
    body = f"<h1>{title}</h1><p><strong>Quality Score: {score}%</strong></p>"
    body += "<ul>"
    for k in ["section_completeness", "keyword_strength", "bullet_quality", "format_compatibility", "content_quantification", "resume_length_score"]:
        v = r.get(k)
        if v is not None:
            body += f"<li>{k.replace('_', ' ').title()}: {v}%</li>"
    body += "</ul><h2>Recommendations</h2><ul>"
    for rec in r.get("recommendations") or []:
        body += f"<li>{rec}</li>"
    body += "</ul>"
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title></head><body>{body}</body></html>"
