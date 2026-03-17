from django.conf import settings
import google.generativeai as genai
from .base import BaseAIProvider, AIResponse
from typing import Optional


class GeminiProvider(BaseAIProvider):

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.AI_MODEL or "gemini-1.5-pro"
        self.model = genai.GenerativeModel(self.model_name)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )

        # Gemini doesn't always return token counts
        input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
        output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

        return AIResponse(
            content=response.text,
            model=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def get_model_name(self) -> str:
        return self.model_name
