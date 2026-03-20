from .config import PromptConfig, LENGTH_GUIDE


class CoverLetterPrompts:

    SYSTEM = """You are an expert career coach who writes compelling, 
personalized cover letters. Your letters are professional but never 
generic. Each letter has a strong opening, clear value proposition, 
and confident closing."""

    @staticmethod
    def build(
        resume_text: str,
        job_description: str,
        config: PromptConfig,
        company_name: str = "",
        job_title: str = "",
    ) -> str:
        lines = [
            f"Tone: {config.tone_description()}",
            LENGTH_GUIDE.get(config.length, LENGTH_GUIDE["standard"]),
        ]

        if company_name:
            lines.append(f"Company: {company_name}")
        if job_title:
            lines.append(f"Role: {job_title}")
        if config.industry:
            lines.append(f"Industry: {config.industry}")
        if config.has_focus_areas():
            lines.append(f"Emphasize: {', '.join(config.focus_areas)}")
        if config.has_custom_instructions():
            lines.append(f"Additional instructions: {config.custom_instructions}")

        context = "\n".join(lines)

        return f"""Write a cover letter based on the resume and job description below.

{context}

Return a JSON object with this exact structure:
{{
    "subject_line": "Application for [Role] at [Company]",
    "opening_paragraph": "...",
    "value_paragraph": "...",
    "alignment_paragraph": "...",
    "closing_paragraph": "...",
    "full_text": "complete letter as a single string"
}}

Resume:
{resume_text}

Job Description:
{job_description}

Return only valid JSON. No explanation. No markdown."""
