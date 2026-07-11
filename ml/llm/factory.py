"""
LLM Factory.

Returns a single shared LLM instance.
"""

from .. import config
from .hf_phi3 import HFPhi3Client
from .qualcomm_phi3 import QualcommPhi3Client

_llm_instance = None


def get_llm():
    """
    Return the configured LLM backend.
    """

    global _llm_instance

    if _llm_instance is None:

        if config.LLM_BACKEND.lower() == "hf":
            _llm_instance = HFPhi3Client()

        elif config.LLM_BACKEND.lower() == "qualcomm":
            _llm_instance = QualcommPhi3Client()

        else:
            raise ValueError(
                f"Unsupported backend: {config.LLM_BACKEND}"
            )

    return _llm_instance