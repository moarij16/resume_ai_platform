from typing import Optional
from django.conf import settings
from google import genai
from google.genai import types
from .base_provider import BaseAIProvider, AIResponse

# Fast and returns valid JSON for our prompts (~2s); gemini-3.8-flash took ~190s per document.
DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Gemini 3.x models think, and thinking tokens count toward max_output_tokens,
# so callers' small output caps would truncate responses.
MIN_MAX_TOKENS = 16000


class GeminiProvider(BaseAIProvider):

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.AI_MODEL or DEFAULT_MODEL

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max(max_tokens, MIN_MAX_TOKENS),
            system_instruction=system_prompt or "",
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        # `text` is None when output was blocked or cut off before any text.
        if not (response.text or "").strip():
            reason = response.candidates[0].finish_reason if response.candidates else None
            raise ValueError(f"Gemini returned no text (finish reason: {reason}).")

        usage = response.usage_metadata
        input_tokens = (usage.prompt_token_count if usage else 0) or 0
        output_tokens = (usage.candidates_token_count if usage else 0) or 0

        return AIResponse(
            content=response.text,
            model=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def get_model_name(self) -> str:
        return self.model_name
