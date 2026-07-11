"""
HuggingFace implementation of the BaseLLMClient.

Development runtime for Microsoft Phi-3 Mini.

This is the ONLY HuggingFace-specific implementation in the project.
Business logic must never appear here.
"""

from __future__ import annotations

import logging

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .. import config
from .base import BaseLLMClient

logger = logging.getLogger(__name__)


class HFPhi3Client(BaseLLMClient):
    """
    HuggingFace implementation for Microsoft Phi-3 Mini.

    Loads the tokenizer and model lazily.
    """

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None

    # ---------------------------------------------------------

    def _lazy_load(self) -> None:
        """
        Load tokenizer and model only once.
        """

        if self._model is not None:
            return

        logger.info("Loading Phi-3 tokenizer...")

        self._tokenizer = AutoTokenizer.from_pretrained(
            config.MODEL_NAME,
            trust_remote_code=True,
        )

        logger.info("Loading Phi-3 model...")

        dtype = (
            torch.bfloat16
            if torch.cuda.is_available()
            else torch.float32
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            config.MODEL_NAME,
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map=config.CPU_DEVICE_MAP,
        )

        logger.info("Phi-3 loaded successfully.")

    # ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Generate a completion from Phi-3.
        """

        self._lazy_load()

        max_new_tokens = (
            max_new_tokens
            if max_new_tokens is not None
            else config.MAX_NEW_TOKENS
        )

        temperature = (
            temperature
            if temperature is not None
            else config.TEMPERATURE
        )

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        print("1. Building input...")

        input_ids = self._tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self._model.device)

        with torch.inference_mode():

          print("2. Starting generation...")

          output = self._model.generate(
             input_ids,
             max_new_tokens=max_new_tokens,
              do_sample=temperature > 0,
             temperature=temperature,
             top_p=config.TOP_P,
             use_cache=config.USE_CACHE,
              pad_token_id=self._tokenizer.eos_token_id,
             eos_token_id=self._tokenizer.eos_token_id,
         )

        print("3. Generation finished.")

        generated = output[0][input_ids.shape[-1]:]

        print("4. Decoding...")

        text = self._tokenizer.decode(
            generated,
            skip_special_tokens=True,
        )

        print("5. Done.")

        return text.strip()