from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    """Standardized response from any AI provider."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class BaseAIProvider(ABC):
    """
    Abstract interface every AI provider must implement.
    Adding a new provider = subclass this and implement generate().
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        """Send a prompt and return a standardized AIResponse."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier being used."""
        pass
