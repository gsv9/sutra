"""
Common benchmarking utilities for the SUTRA AI Copilot.

Shared by:
    - benchmark_cpu.py
    - benchmark_qnn.py
    - benchmark_sutra.py
    - compare_results.py
"""

from __future__ import annotations

import csv
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------


class Timer:
    """
    High-resolution timer.
    """

    def __init__(self) -> None:
        self._start = 0.0

    def start(self) -> None:
        self._start = time.perf_counter()

    def stop(self) -> float:
        """
        Returns elapsed time in milliseconds.
        """
        return (time.perf_counter() - self._start) * 1000.0


# ---------------------------------------------------------------------
# Benchmark Result
# ---------------------------------------------------------------------


@dataclass
class BenchmarkResult:
    """
    Standard benchmark result shared by all benchmarks.
    """

    benchmark: str
    model: str
    execution_provider: str

    load_time_ms: float
    inference_time_ms: float
    total_time_ms: float

    prompt_tokens: int
    output_tokens: int

    tokens_per_second: float


# ---------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------


def warmup(function, runs: int = 1) -> None:
    """
    Execute warm-up runs before measuring performance.
    """

    for _ in range(runs):
        function()


# ---------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------


def print_result(result: BenchmarkResult) -> None:

    print()
    print("=" * 72)
    print(f"Benchmark : {result.benchmark}")
    print("=" * 72)

    print(f"Model                : {result.model}")
    print(f"Execution Provider   : {result.execution_provider}")
    print()

    print(f"Prompt Tokens        : {result.prompt_tokens}")
    print(f"Output Tokens        : {result.output_tokens}")
    print()

    print(f"Load Time            : {result.load_time_ms:.2f} ms")
    print(f"Inference Time       : {result.inference_time_ms:.2f} ms")
    print(f"Total Time           : {result.total_time_ms:.2f} ms")
    print()

    print(f"Tokens / Second      : {result.tokens_per_second:.2f}")

    print("=" * 72)
    print()


# ---------------------------------------------------------------------
# Save Results
# ---------------------------------------------------------------------


def save_results(
    results: list[BenchmarkResult],
    filename: str,
) -> None:
    """
    Save benchmark results as CSV and JSON.
    """

    if not results:
        return

    csv_path = RESULTS_DIR / f"{filename}.csv"
    json_path = RESULTS_DIR / f"{filename}.json"

    # CSV

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=asdict(results[0]).keys(),
        )

        writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))

    # JSON

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            [asdict(result) for result in results],
            file,
            indent=4,
        )

    print(f"Saved CSV  : {csv_path}")
    print(f"Saved JSON : {json_path}")


# ---------------------------------------------------------------------
# Comparison Table
# ---------------------------------------------------------------------


def print_comparison(
    results: list[BenchmarkResult],
) -> None:

    print()
    print("=" * 120)

    print(
        f"{'Benchmark':18}"
        f"{'Provider':24}"
        f"{'Load(ms)':>12}"
        f"{'Infer(ms)':>14}"
        f"{'Total(ms)':>14}"
        f"{'Tok/s':>12}"
    )

    print("-" * 120)

    for result in results:

        print(
            f"{result.benchmark:18}"
            f"{result.execution_provider:24}"
            f"{result.load_time_ms:12.2f}"
            f"{result.inference_time_ms:14.2f}"
            f"{result.total_time_ms:14.2f}"
            f"{result.tokens_per_second:12.2f}"
        )

    print("=" * 120)
    print()


# ---------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------


def compute_statistics(values: list[float]) -> dict[str, float]:
    """
    Compute summary statistics for repeated benchmark runs.
    """

    if not values:

        return {
            "mean": 0.0,
            "median": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "stddev": 0.0,
        }

    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "stddev": (
            statistics.stdev(values)
            if len(values) > 1
            else 0.0
        ),
    }