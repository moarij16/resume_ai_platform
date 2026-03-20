import json

from core.ai.service import AIService
from core.ai.parser import AIResponseParser
from core.ai.exceptions import AIGenerationFailed


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
    """
    ai = AIService()

    try:
        response = ai.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise AIGenerationFailed(detail=str(e))

    parser = AIResponseParser()
    try:
        parsed = parser.parse_json(response.content)
        if response_key is not None:
            return parsed.get(response_key, response.content)
        return json.dumps(parsed)
    except ValueError:
        return response.content
