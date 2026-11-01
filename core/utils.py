def get_resume_text(resume) -> str:
    """Extract plain text from a Resume instance's resume_data for use in prompts/scanning."""
    data = resume.resume_data or {}

    if data.get("raw_text"):
        return data["raw_text"]

    parts = []
    if data.get("summary"):
        parts.append(data["summary"])
    for exp in data.get("experience", []):
        parts.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
        parts.extend(exp.get("bullets", []))
    parts.extend(data.get("skills", []))
    for edu in data.get("education", []):
        parts.append(f"{edu.get('degree', '')} {edu.get('institution', '')}")
    return "\n".join(parts)
