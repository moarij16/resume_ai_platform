from django.conf import settings
from .base_provider import BaseAIProvider, AIResponse
from typing import Optional


def get_provider() -> BaseAIProvider:
    """
    Factory — returns the correct provider based on AI_PROVIDER setting.
    Swap providers by changing AI_PROVIDER in .env — no code changes needed.
    """
    provider = settings.AI_PROVIDER.lower()

    if provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    elif provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    elif provider == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider()
    else:
        raise ValueError(
            f"Unknown AI provider: {provider}. Choose openai, anthropic, or gemini."
        )


class AIService:
    """
    Single entry point for all AI calls in the project.
    Views and services never import providers directly — only this class.

    Usage:
        from services.ai.service import AIService
        ai = AIService()
        response = ai.generate(prompt="...", system_prompt="...")
        print(response.content)
    """

    def __init__(self):
        self.provider: BaseAIProvider = get_provider()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        return self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @property
    def model_name(self) -> str:
        return self.provider.get_model_name()
