import json
import re
from typing import Any


class AIResponseParser:
    """
    Safely parses JSON from AI responses.
    Handles markdown code blocks AI providers sometimes wrap responses in.
    """

    @staticmethod
    def parse_json(content: str) -> dict[str, Any]:
        cleaned = re.sub(r"```json\s*", "", content)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse JSON from AI response: {content[:200]}")
