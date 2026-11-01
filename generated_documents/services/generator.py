"""
Document generation service.
All generation functions follow the same pattern:
  1. Fetch models
  2. Build PromptConfig from user inputs
  3. Build prompt string
  4. Call _call_ai()
  5. Save GeneratedDocument and return
"""

from resumes.models import Resume
from jobs.models import JobDescription
from generated_documents.models import GeneratedDocument, DocumentType
from core.utils import get_resume_text

from core.ai.prompts import (
    CoverLetterPrompts,
    LinkedInPrompts,
    ResumePrompts,
    PromptConfig,
)
from generated_documents.services.utils import call_ai


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
        resume_text=get_resume_text(resume),
        job_description=job.job_description_text if job else "",
        config=config,
        company_name=company_name or (job.company_name if job else ""),
        job_title=job_title or (job.job_title if job else ""),
    )

    content = call_ai(
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
        resume_text=get_resume_text(resume),
        config=config,
    )

    content = call_ai(
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
        resume_text=get_resume_text(resume),
        config=config,
        job_description=job.job_description_text if job else "",
    )

    content = call_ai(
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
        resume_text=get_resume_text(resume),
        config=config,
        job_description=job.job_description_text if job else "",
    )

    content = call_ai(
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
