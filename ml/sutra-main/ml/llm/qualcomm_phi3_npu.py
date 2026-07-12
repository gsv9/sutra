"""
Qualcomm Snapdragon NPU backend.

Uses Windows ML Runtime + Qualcomm QNN EP.
"""

from __future__ import annotations

from pathlib import Path

import onnxruntime_genai as og

try:
    import windowsml
except Exception:
    windowsml = None

from .. import config
from .base import BaseLLMClient


class QualcommPhi3NPUClient(BaseLLMClient):

    def __init__(self):

        self._loaded = False

    # ----------------------------------------------------

    def _lazy_load(self):

        if self._loaded:
            return

        model_path = (
            Path(__file__).resolve().parents[2]
            / "models"
            / "phi3-onnx"
            / "cpu_and_mobile"
            / "cpu-int4-rtn-block-32-acc-level-4"
        )

        cfg = og.Config(str(model_path))

        qnn_ready = False

        if windowsml is not None:
            try:
                catalog = windowsml.EpCatalog()
                providers = catalog.find_all_providers()
                qnn = next(
                    p for p in providers
                    if p.name == "QNNExecutionProvider"
                )

                qnn.ensure_ready()

                og.register_execution_provider_library(
                    "QNNExecutionProvider",
                    qnn.library_path,
                )

                cfg.clear_providers()
                cfg.append_provider("QNNExecutionProvider")
                qnn_ready = True

            except Exception as exc:
                print(
                    "[LLM] QNN provider not available; "
                    f"falling back to default providers ({exc})"
                )

        if not qnn_ready:
            print("[LLM] Using default ONNX Runtime providers")

        self.model = og.Model(cfg)

        self.tokenizer = og.Tokenizer(self.model)

        self.stream = self.tokenizer.create_stream()

        self._loaded = True

    # ----------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:

        self._lazy_load()

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        try:

            prompt = self.tokenizer.apply_chat_template(
                messages=messages,
                add_generation_prompt=True,
            )

        except Exception:
            prompt = f"{system_prompt}\n\n{user_prompt}".strip()

        input_tokens = self.tokenizer.encode(prompt)

        params = og.GeneratorParams(self.model)

        params.set_search_options(
            max_length=len(input_tokens) + (max_new_tokens if max_new_tokens else config.MAX_NEW_TOKENS),
            temperature=0.1,
            do_sample=True,
            top_p=0.8,
            repetition_penalty=1.1,
        )

        generator = og.Generator(
            self.model,
            params,
        )

        generator.append_tokens(input_tokens)

        output = []

        while not generator.is_done():

            generator.generate_next_token()

            token = generator.get_next_tokens()[0]

            output.append(
                self.stream.decode(token)
            )

        return "".join(output).strip()
