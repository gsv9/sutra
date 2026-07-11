"""
Abstract interface for every Large Language Model backend.
"""

from abc import ABC
from abc import abstractmethod


class BaseLLMClient(ABC):
    """
    Every inference runtime must implement this interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Generate a response from the model.

        Args:
            prompt:
                Complete prompt.

            max_new_tokens:
                Override default generation length.

            temperature:
                Override default temperature.

        Returns
        -------
        Raw model output.
        """
        raise NotImplementedError