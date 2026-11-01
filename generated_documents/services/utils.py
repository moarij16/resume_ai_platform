import json
import logging

from core.ai.service import AIService
from core.ai.parser import AIResponseParser
from core.ai.exceptions import AIGenerationFailed, AIRateLimited

logger = logging.getLogger(__name__)


def _is_rate_limit(error: Exception) -> bool:
    """OpenAI/Anthropic errors carry `status_code`; Google GenAI errors carry `code`."""
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    return status == 429


def call_ai(
    prompt: str,
    system_prompt: str,
    response_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Single point of contact for all AI calls in this service.
    Wraps generation, parsing, and error handling.

    If response_key is given, extracts that key from the parsed JSON.
    If response_key is None, returns the full parsed JSON as a string
    so no fields are silently dropped.

    Provider failures become friendly 503s (AIProviderNotConfigured,
    AIRateLimited, AIGenerationFailed); the provider's own error text is only
    logged, never returned to the client.
    """
    ai = AIService()  # raises AIProviderNotConfigured if the provider isn't set up

    try:
        response = ai.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        logger.exception("AI generation failed (model=%s)", ai.model_name)
        if _is_rate_limit(e):
            raise AIRateLimited() from e
        raise AIGenerationFailed() from e

    parser = AIResponseParser()
    try:
        parsed = parser.parse_json(response.content)
        if response_key is not None:
            return parsed.get(response_key, response.content)
        return json.dumps(parsed)
    except ValueError:
        return response.content
