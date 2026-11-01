"""
Extract experience-related entities: companies, job titles, dates, total years.
Uses section detection + experience parser + optional NER.
"""

from typing import Any

from .section_detector import detect_sections
from .experience_parser import parse_experience
from ..utils.logger import get_logger

logger = get_logger(__name__)


def extract_experience_entities(text: str) -> dict[str, Any]:
    """
    Extract companies, job titles, date ranges, and total years from resume.

    Returns:
        companies: list of company names
        job_titles: list of job titles
        dates: list of (start, end) date strings
        total_years: float
    """
    exp = parse_experience(text)
    experiences = exp.get("experiences", [])
    companies = list(dict.fromkeys(e.get("company") for e in experiences if e.get("company")))
    job_titles = list(dict.fromkeys(e.get("title") for e in experiences if e.get("title")))
    dates = [
        (str(e.get("start_year") or ""), str(e.get("end_year") or ""))
        for e in experiences
    ]
    total_years = exp.get("total_years", 0)
    return {
        "companies": companies,
        "job_titles": job_titles,
        "dates": dates,
        "total_years": total_years,
        "experiences": experiences,
    }
