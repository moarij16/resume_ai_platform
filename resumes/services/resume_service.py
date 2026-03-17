"""
Resume file upload and parsing service.

Saves the uploaded file via Django's default_storage (local disk or Supabase S3
depending on settings) and parses it using scanner.
"""

import tempfile
import uuid
from pathlib import Path

from django.core.files.storage import default_storage

from scanner.parsers import parse_resume
from scanner.processors.skill_extractor import extract_skills_context_aware
from scanner.analyzers.section_detector import detect_sections
from scanner.analyzers.content_analyzer import analyze_bullets
from scanner.analyzers.experience_parser import parse_experience


def upload_and_parse(user, file) -> dict:
    """
    Upload a resume file via default_storage and parse it with scanner.

    Args:
        user: Users instance (the authenticated user).
        file: Django InMemoryUploadedFile / UploadedFile from request.FILES.

    Returns:
        dict with keys:
          - file_url: storage URL to the saved file
          - parsed_data: structured dict ready to store in Resume.resume_data
    """
    ext = Path(file.name).suffix.lower()
    filename = f"{user.id}_{uuid.uuid4().hex}{ext}"
    storage_path = f"resumes/{filename}"

    # Parse before uploading — file is still in memory, no need to re-download
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    parsed = parse_resume(tmp_path)
    text = parsed["text"]
    metadata = parsed["metadata"]

    skills_data = extract_skills_context_aware(text)
    sections = detect_sections(text)
    bullets = analyze_bullets(text)
    experience = parse_experience(text)

    parsed_data = {
        "raw_text": text,
        "word_count": len(text.split()),
        "metadata": metadata,
        "sections": sections,
        "detected_skills": skills_data.get("detected_skills", []),
        "skills_detail": skills_data.get("skills", {}),
        "bullets": bullets,
        "experience": experience,
    }

    # Upload to storage (local disk or Supabase S3)
    file.seek(0)
    saved_path = default_storage.save(storage_path, file)
    file_url = default_storage.url(saved_path)

    return {"file_url": file_url, "parsed_data": parsed_data}
