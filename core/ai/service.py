import logging

from django.conf import settings
from .base_provider import BaseAIProvider, AIResponse
from .exceptions import AIProviderNotConfigured
from typing import Optional

logger = logging.getLogger(__name__)

# The settings key each provider needs; a missing key fails fast with a clear
# server-side log instead of a provider 401 surfacing to the user.
API_KEY_SETTINGS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def get_provider() -> BaseAIProvider:
    """
    Factory — returns the correct provider based on AI_PROVIDER setting.
    Swap providers by changing AI_PROVIDER in .env — no code changes needed.
    Raises AIProviderNotConfigured (HTTP 503) when the provider is unknown or
    its API key is missing.
    """
    provider = settings.AI_PROVIDER.lower()

    key_setting = API_KEY_SETTINGS.get(provider)
    if key_setting is None:
        logger.error("Unknown AI_PROVIDER %r. Choose openai, anthropic, or gemini.", provider)
        raise AIProviderNotConfigured()
    if not getattr(settings, key_setting, ""):
        logger.error("AI_PROVIDER=%s but %s is not set.", provider, key_setting)
        raise AIProviderNotConfigured()

    if provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    elif provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    elif provider == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider()


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
