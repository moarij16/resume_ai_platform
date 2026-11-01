from resumes.models import Resume
from jobs.models import JobDescription
from ats.models import ATSScan, ScanMode
from scanner.scorers import score_resume_vs_jd
from scanner.models import analyze_resume_quality
from core.utils import get_resume_text


def run_scan(user, resume_id, job_id=None) -> ATSScan:
    """
    Run ATS scan.
    - resume_id only → Mode 2: resume quality analysis
    - resume_id + job_id → Mode 1: resume vs JD match
    """
    resume = Resume.objects.get(id=resume_id, user=user)
    job = JobDescription.objects.get(id=job_id, user=user) if job_id else None

    resume_text = get_resume_text(resume)

    if job:
        result = score_resume_vs_jd(resume_text, job.job_description_text)
        score = result["ats_score"]
        breakdown = result.get("breakdown", {})
        missing = result.get("missing_critical_skills", [])
        suggestions = result.get("recommendations", []) + [
            r.get("action", "")
            for r in result.get("actionable_recommendations", [])
            if r.get("action")
        ]
        mode = ScanMode.JD_MATCH
    else:
        result = analyze_resume_quality(resume_text)
        score = result["quality_score"]
        breakdown = {
            "section_completeness": result.get("section_completeness"),
            "keyword_strength": result.get("keyword_strength"),
            "bullet_quality": result.get("bullet_quality"),
            "format_compatibility": result.get("format_compatibility"),
            "content_quantification": result.get("content_quantification"),
            "resume_length": result.get("resume_length"),
        }
        missing = []
        suggestions = result.get("recommendations", [])
        mode = ScanMode.RESUME_ONLY

    return ATSScan.create_for_user(
        user=user,
        resume=resume,
        job=job,
        scan_mode=mode,
        ats_score=score,
        breakdown=breakdown,
        missing_keywords=missing,
        suggestions=suggestions,
        scan_result=result,
    )
