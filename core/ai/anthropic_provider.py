from django.conf import settings
from anthropic import Anthropic
from .base_provider import BaseAIProvider, AIResponse
from typing import Optional

DEFAULT_MODEL = "claude-sonnet-5-5"

# Thinking is on by default for current Claude models and its tokens count
# toward max_tokens, so callers' small output caps would truncate responses.
MIN_MAX_TOKENS = 16000

# Document generation is plain content writing; "low" is the recommended
# starting effort for it. Raise it here if output quality needs it.
EFFORT = "low"

# Models that support server-side refusal fallback (`fallbacks: "default"`):
# a false-positive safety decline is retried on another model, not failed.
FALLBACK_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider(BaseAIProvider):

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.AI_MODEL or DEFAULT_MODEL

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        # `temperature` is accepted for interface compatibility but not sent:
        # the Messages API rejects sampling parameters on current models.
        kwargs = {
            "model": self.model,
            "max_tokens": max(max_tokens, MIN_MAX_TOKENS),
            "output_config": {"effort": EFFORT},
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if self.model in FALLBACK_MODELS:
            response = self.client.beta.messages.create(
                betas=[FALLBACK_BETA], fallbacks="default", **kwargs
            )
        else:
            response = self.client.messages.create(**kwargs)

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise ValueError(f"Claude declined the request (category: {category}).")
        if response.stop_reason == "max_tokens":
            raise ValueError("Claude's response was cut off at the max_tokens limit.")

        # The content list can hold thinking blocks before the answer; keep only text.
        content = "".join(block.text for block in response.content if block.type == "text")
        if not content.strip():
            raise ValueError("Claude returned no text content.")

        return AIResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )

    def get_model_name(self) -> str:
        return self.model
