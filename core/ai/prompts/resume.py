from .config import PromptConfig


class ResumePrompts:

    SYSTEM = """You are an expert resume writer with 15 years of experience.
You write clear, concise, and impactful resumes that pass ATS systems
and impress recruiters. Use strong action verbs. Quantify achievements.
Never use personal pronouns."""

    @staticmethod
    def build(
        resume_text: str,
        config: PromptConfig,
        job_description: str = "",
    ) -> str:
        lines = [f"Tone: {config.tone_description()}"]

        if config.has_focus_areas():
            lines.append(f"Emphasize: {', '.join(config.focus_areas)}")
        if config.years_experience:
            lines.append(
                f"Candidate has {config.years_experience} years of experience. "
                f"Frame achievements accordingly."
            )
        if config.has_custom_instructions():
            lines.append(f"Additional instructions: {config.custom_instructions}")
        if job_description:
            lines.append(
                f"\nTarget Job Description:\n{job_description}\n"
                f"Tailor the resume to align with this role."
            )

        context = "\n".join(lines)

        return f"""Rewrite and improve the following resume.

{context}

Return a JSON object with this exact structure:
{{
    "summary": "professional summary paragraph",
    "experience": [
        {{
            "title": "job title",
            "company": "company name",
            "duration": "start - end",
            "bullets": ["achievement 1", "achievement 2"]
        }}
    ],
    "education": [
        {{
            "degree": "degree name",
            "institution": "school name",
            "year": "graduation year"
        }}
    ],
    "skills": ["skill1", "skill2"],
    "improvements_made": ["change 1", "change 2"]
}}

Original Resume:
{resume_text}

Return only valid JSON. No explanation. No markdown."""
