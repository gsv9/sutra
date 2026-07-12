"""
Inference metrics for the SUTRA AI Copilot.

Collects lightweight runtime statistics for benchmarking and
hackathon demonstrations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class InferenceMetrics:
    """
    Runtime metrics captured for each inference.
    """

    backend: str
    latency_ms: float
    prompt_length: int
    response_length: int


class MetricsRecorder:
    """
    Records inference latency.
    """

    def __init__(self):

        self._start = 0.0

    def start(self):

        self._start = time.perf_counter()

    def stop(
        self,
        backend: str,
        prompt: str,
        response: str,
    ) -> InferenceMetrics:

        latency = (
            time.perf_counter() - self._start
        ) * 1000

        return InferenceMetrics(
            backend=backend,
            latency_ms=round(latency, 2),
            prompt_length=len(prompt),
            response_length=len(response),
        )