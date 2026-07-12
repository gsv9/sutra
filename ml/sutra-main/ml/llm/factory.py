"""
LLM Factory.

Creates and returns a shared LLM backend instance.
"""

from __future__ import annotations

from .base import BaseLLMClient
from .. import config


_llm_instance: BaseLLMClient | None = None


def get_llm() -> BaseLLMClient:
    """
    Return the configured LLM backend.

    The backend is instantiated only once and shared for the
    lifetime of the application.
    """

    global _llm_instance

    if _llm_instance is None:

        backend = config.LLM_BACKEND.lower()

        if backend == "hf":
            from .hf_phi3 import HFPhi3Client

            _llm_instance = HFPhi3Client()

        elif backend == "qualcomm":
            from .qualcomm_phi3 import QualcommPhi3Client

            _llm_instance = QualcommPhi3Client()

        else:
            raise ValueError(
                f"Unsupported LLM backend: {config.LLM_BACKEND}"
            )

    return _llm_instance
