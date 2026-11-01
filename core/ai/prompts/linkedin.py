from .config import PromptConfig


class LinkedInPrompts:

    SYSTEM = """You are a LinkedIn profile optimization expert.
You write headlines and summaries that attract recruiters and
authentically represent the professional. Use keywords naturally.
Write in first person."""

    @staticmethod
    def build(resume_text: str, config: PromptConfig) -> str:
        lines = [f"Tone: {config.tone_description()}"]

        if config.has_focus_areas():
            lines.append(f"Highlight: {', '.join(config.focus_areas)}")
        if config.has_custom_instructions():
            lines.append(f"Additional instructions: {config.custom_instructions}")

        context = "\n".join(lines)

        return f"""Generate a LinkedIn profile based on the resume below.

{context}

Return a JSON object with this exact structure:
{{
    "headline": "LinkedIn headline under 120 characters",
    "summary": "About section 3-5 sentences",
    "skills": ["skill1", "skill2", "skill3"],
    "headline_alternatives": ["alt 1", "alt 2", "alt 3"]
}}

Resume:
{resume_text}

Return only valid JSON. No explanation. No markdown."""
