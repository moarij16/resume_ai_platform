from dataclasses import dataclass, field


class Tone:
    PROFESSIONAL = "professional"
    CONFIDENT = "confident"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"

    ALL = [
        PROFESSIONAL,
        CONFIDENT,
        CONVERSATIONAL,
        FORMAL,
        TECHNICAL,
        EXECUTIVE,
    ]

    DESCRIPTIONS = {
        PROFESSIONAL: "clear, polished, and professional",
        CONFIDENT: "assertive, direct, and results-focused",
        CONVERSATIONAL: "warm, approachable, and natural",
        FORMAL: "formal and traditional — suited for conservative industries",
        TECHNICAL: "precise, technical, and detail-oriented",
        EXECUTIVE: "strategic, leadership-focused, and high-level",
    }


LENGTH_GUIDE = {
    "brief": "Keep it concise — 150-200 words maximum.",
    "standard": "Standard length — 250-350 words.",
    "detailed": "Thorough and detailed — 400-500 words.",
}


@dataclass
class PromptConfig:
    tone: str = Tone.PROFESSIONAL
    custom_instructions: str = ""
    focus_areas: list[str] = field(default_factory=list)
    length: str = "standard"
    industry: str = ""
    years_experience: int = 0

    def tone_description(self) -> str:
        return Tone.DESCRIPTIONS.get(self.tone, Tone.DESCRIPTIONS[Tone.PROFESSIONAL])

    def has_custom_instructions(self) -> bool:
        return bool(self.custom_instructions.strip())

    def has_focus_areas(self) -> bool:
        return bool(self.focus_areas)
