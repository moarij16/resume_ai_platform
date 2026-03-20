"""
Document generation service.
All generation functions follow the same pattern:
  1. Fetch models
  2. Build PromptConfig from user inputs
  3. Build prompt string
  4. Call _call_ai()
  5. Save GeneratedDocument and return
"""

import json

from resumes.models import Resume
from jobs.models import JobDescription
from generated_documents.models import GeneratedDocument, DocumentType
from core.ai.service import AIService
from core.ai.parser import AIResponseParser
from core.ai.exceptions import AIGenerationFailed
from core.ai.prompts import (
    CoverLetterPrompts,
    LinkedInPrompts,
    ResumePrompts,
    PromptConfig,
)


# ── Cover Letter ──────────────────────────────────────────────────────


def generate_cover_letter(
    user,
    resume_id,
    job_id=None,
    tone="professional",
    custom_instructions="",
    focus_areas=None,
    length="standard",
    industry="",
    company_name="",
    job_title="",
) -> GeneratedDocument:

    resume = Resume.objects.get(id=resume_id, user=user)
    job = JobDescription.objects.get(id=job_id, user=user) if job_id else None

    config = PromptConfig(
        tone=tone,
        custom_instructions=custom_instructions,
        focus_areas=focus_areas or [],
        length=length,
        industry=industry,
    )

    prompt = CoverLetterPrompts.build(
        resume_text=_get_resume_text(resume),
        job_description=job.job_description_text if job else "",
        config=config,
        company_name=company_name or (job.company_name if job else ""),
        job_title=job_title or (job.job_title if job else ""),
    )

    content = _call_ai(
        prompt=prompt,
        system_prompt=CoverLetterPrompts.SYSTEM,
        response_key="full_text",
    )

    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.COVER_LETTER,
        document_content=content,
        resume=resume,
        job=job,
    )


# ── LinkedIn Bio ──────────────────────────────────────────────────────


def generate_linkedin_bio(
    user,
    resume_id,
    tone="professional",
    custom_instructions="",
    focus_areas=None,
) -> GeneratedDocument:

    resume = Resume.objects.get(id=resume_id, user=user)

    config = PromptConfig(
        tone=tone,
        custom_instructions=custom_instructions,
        focus_areas=focus_areas or [],
    )

    prompt = LinkedInPrompts.build(
        resume_text=_get_resume_text(resume),
        config=config,
    )

    content = _call_ai(
        prompt=prompt,
        system_prompt=LinkedInPrompts.SYSTEM,
    )

    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.LINKED_IN_BIO,
        document_content=content,
        resume=resume,
    )


# ── Resume Generation ─────────────────────────────────────────────────


def generate_resume(
    user,
    resume_id,
    job_id=None,
    tone="professional",
    custom_instructions="",
    focus_areas=None,
    length="standard",
    industry="",
) -> GeneratedDocument:

    resume = Resume.objects.get(id=resume_id, user=user)
    job = JobDescription.objects.get(id=job_id, user=user) if job_id else None

    config = PromptConfig(
        tone=tone,
        custom_instructions=custom_instructions,
        focus_areas=focus_areas or [],
        length=length,
        industry=industry,
    )

    prompt = ResumePrompts.build(
        resume_text=_get_resume_text(resume),
        config=config,
        job_description=job.job_description_text if job else "",
    )

    content = _call_ai(
        prompt=prompt,
        system_prompt=ResumePrompts.SYSTEM,
        temperature=0.5,
        max_tokens=3000,
    )

    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.RESUME,
        document_content=content,
        resume=resume,
        job=job,
    )


# ── Resume Refactor ───────────────────────────────────────────────────


def generate_resume_refactor(
    user,
    resume_id,
    job_id=None,
    tone="professional",
    custom_instructions="",
    focus_areas=None,
) -> GeneratedDocument:

    resume = Resume.objects.get(id=resume_id, user=user)
    job = JobDescription.objects.get(id=job_id, user=user) if job_id else None

    config = PromptConfig(
        tone=tone,
        custom_instructions=custom_instructions,
        focus_areas=focus_areas or [],
    )

    prompt = ResumePrompts.build(
        resume_text=_get_resume_text(resume),
        config=config,
        job_description=job.job_description_text if job else "",
    )

    content = _call_ai(
        prompt=prompt,
        system_prompt=ResumePrompts.SYSTEM,
        temperature=0.5,
        max_tokens=3000,
    )

    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.RESUME_REFACTOR,
        document_content=content,
        resume=resume,
        job=job,
    )


# ── Shared helpers ────────────────────────────────────────────────────


def _call_ai(
    prompt: str,
    system_prompt: str,
    response_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Single point of contact for all AI calls in this service.
    Wraps generation, parsing, and error handling.

    If response_key is given, extracts that key from the parsed JSON.
    If response_key is None, returns the full parsed JSON as a string
    so no fields are silently dropped.
    """
    ai = AIService()

    try:
        response = ai.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise AIGenerationFailed(detail=str(e))

    parser = AIResponseParser()
    try:
        parsed = parser.parse_json(response.content)
        if response_key is not None:
            return parsed.get(response_key, response.content)
        return json.dumps(parsed)
    except ValueError:
        return response.content


def _get_resume_text(resume: Resume) -> str:
    """Extract plain text from resume data for use in prompts."""
    data = resume.resume_data or {}

    if "raw_text" in data:
        return data["raw_text"]

    parts = []
    if data.get("summary"):
        parts.append(data["summary"])
    for exp in data.get("experience", []):
        parts.append(f"{exp.get('title')} at {exp.get('company')}")
        parts.extend(exp.get("bullets", []))
    parts.extend(data.get("skills", []))
    return "\n".join(parts)
