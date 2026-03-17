"""
Contact information extraction and validation.

Extracts and validates email, phone, LinkedIn, GitHub/portfolio URLs,
and location (city, state, country).
"""

import re
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Patterns
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
LINKEDIN_PATTERN = re.compile(
    r"https?://(?:www\.)?linkedin\.com/in/[\w\-./]+",
    re.IGNORECASE,
)
GITHUB_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/[\w\-]+",
    re.IGNORECASE,
)
GENERIC_URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+",
    re.IGNORECASE,
)
# Simple US/International phone: digits, spaces, dashes, dots, optional + at start
PHONE_CANDIDATE = re.compile(
    r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{0,6}"
)


def _validate_email(email: str) -> bool:
    """Validate email format and basic structure."""
    try:
        from email_validator import validate_email
        validate_email(email, check_deliverability=False)
        return True
    except Exception:
        return False


def _validate_phone(phone: str) -> tuple[bool, str | None]:
    """
    Validate and format phone number. Returns (is_valid, normalized_or_none).
    """
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            return True, phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        return False, None
    except Exception:
        return False, None


def extract_contacts(text: str) -> dict[str, Any]:
    """
    Extract and validate contact information from text.

    Args:
        text: Resume or document text.

    Returns:
        Dictionary with keys: email, phone, phone_normalized, linkedin, github,
        portfolio_urls, location (dict with city, state, country if detected).
    """
    result: dict[str, Any] = {
        "email": None,
        "phone": None,
        "phone_normalized": None,
        "linkedin": None,
        "github": None,
        "portfolio_urls": [],
        "location": {"city": None, "state": None, "country": None},
    }

    # Email
    emails = EMAIL_PATTERN.findall(text)
    for e in emails:
        if _validate_email(e):
            result["email"] = e
            break
    if not result["email"] and emails:
        result["email"] = emails[0]  # best effort

    # LinkedIn
    linkedin = LINKEDIN_PATTERN.findall(text)
    if linkedin:
        result["linkedin"] = linkedin[0].rstrip("/")

    # GitHub
    github = GITHUB_PATTERN.findall(text)
    if github:
        result["github"] = github[0].rstrip("/")

    # Other URLs (portfolio-like)
    all_urls = GENERIC_URL_PATTERN.findall(text)
    skip = {result.get("linkedin"), result.get("github")}
    result["portfolio_urls"] = [
        u for u in all_urls
        if u not in skip
        and "linkedin.com" not in u.lower()
        and "github.com" not in u.lower()
    ][:5]

    # Phone
    for match in PHONE_CANDIDATE.finditer(text):
        candidate = match.group(0).strip()
        if len(re.sub(r"\D", "", candidate)) >= 10:
            valid, normalized = _validate_phone(candidate)
            if valid and normalized:
                result["phone"] = candidate
                result["phone_normalized"] = normalized
                break

    # Location: simple heuristic - look for "City, State" or "City, Country"
    # Use first line that looks like address (comma-separated, mixed case)
    location_line = re.search(
        r"(?:^|\n)\s*([A-Za-z][A-Za-z\s]+(?:,\s*[A-Za-z][A-Za-z\s]*){1,2})\s*(?:\n|$)",
        text,
    )
    if location_line:
        parts = [p.strip() for p in location_line.group(1).split(",")]
        if len(parts) >= 1:
            result["location"]["city"] = parts[0]
        if len(parts) >= 2:
            result["location"]["state"] = parts[1]
        if len(parts) >= 3:
            result["location"]["country"] = parts[2]

    return result
