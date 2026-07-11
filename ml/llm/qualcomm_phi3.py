"""
Qualcomm Snapdragon AI PC runtime.

This class is the only module that will change when migrating from
HuggingFace to Qualcomm AI Hub / QNN Runtime.
"""

from __future__ import annotations

from .base import BaseLLMClient


class QualcommPhi3Client(BaseLLMClient):
    """
    Qualcomm NPU implementation placeholder.

    The interface is intentionally identical to HFPhi3Client so that
    business logic remains unchanged.
    """

    def __init__(self) -> None:
        self._loaded = False

    def _lazy_load(self) -> None:
        """
        TODO:
        - Load AI Hub exported model.
        - Initialize QNN Runtime.
        - Allocate NPU buffers.
        """
        if self._loaded:
            return

        self._loaded = True

    def generate(
        self,
        prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:

        self._lazy_load()

        raise NotImplementedError(
            "Qualcomm AI Hub runtime will be implemented on the Snapdragon AI PC."
        )