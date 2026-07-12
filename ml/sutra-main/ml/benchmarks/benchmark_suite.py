"""
Comprehensive benchmark suite for the SUTRA AI Copilot.

Run

    python -m ml.benchmarks.benchmark_suite
"""

from __future__ import annotations

import csv
import json
import statistics
import time
from pathlib import Path

from ml.agent import InventoryAgent, run_inference

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

WARM_RUNS = 5

CONTEXT = {
    "item": "Rice",
    "remaining_weight": 3.4,
    "reorder_threshold": 5,
    "unit": "kg",
    "avg_daily_sales": 14.5,
    "sales_trend": [12, 15, 11, 18, 22, 19],
    "suppliers": [
        {
            "supplier_name": "ABC Traders",
            "price_per_unit": 42,
            "reliability_score": 97,
            "lead_time_days": 1,
        },
        {
            "supplier_name": "XYZ Wholesale",
            "price_per_unit": 44,
            "reliability_score": 78,
            "lead_time_days": 3,
        },
    ],
    "upcoming_festivals": [
        {
            "name": "Local Festival",
            "days_away": 3,
        }
    ],
    "timestamp": "2026-07-11T11:34:01",
}

QUESTIONS = [
    "Why reorder now?",
    "Why ABC Traders?",
    "Compare suppliers.",
    "Can I wait two days?",
    "What if festival is cancelled?",
    "How confident are you?",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def stats(values):

    return {
        "runs": len(values),
        "mean_ms": round(statistics.mean(values), 2),
        "median_ms": round(statistics.median(values), 2),
        "minimum_ms": round(min(values), 2),
        "maximum_ms": round(max(values), 2),
        "stddev_ms": round(
            statistics.stdev(values),
            2,
        )
        if len(values) > 1
        else 0.0,
    }


# ---------------------------------------------------------------------
# Recommendation Benchmark
# ---------------------------------------------------------------------


def benchmark_recommendation():

    start = time.perf_counter()

    state = run_inference(
        CONTEXT,
        return_state=True,
    )

    elapsed = (
        time.perf_counter() - start
    ) * 1000

    return state, elapsed


# ---------------------------------------------------------------------
# Conversation Benchmark
# ---------------------------------------------------------------------


def benchmark_conversation(agent, state):

    results = []

    for question in QUESTIONS:

        start = time.perf_counter()

        answer = agent.chat(
            question=question,
            state=state,
            context=CONTEXT,
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        print()

        print("-" * 70)
        print(question)
        print(f"{elapsed:.2f} ms")
        print(answer[:120].replace("\n", " "), "...")

        results.append(
            {
                "question": question,
                "latency_ms": round(elapsed, 2),
            }
        )

    return results


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main():

    print()
    print("=" * 80)
    print("SUTRA AI BENCHMARK SUITE")
    print("=" * 80)

    # -------------------------------------------------------------

    print("\nCold Recommendation\n")

    _, cold = benchmark_recommendation()

    print(f"{cold:.2f} ms")

    # -------------------------------------------------------------

    warm_runs = []

    state = None

    print("\nWarm Recommendation Runs\n")

    for i in range(WARM_RUNS):

        state, latency = benchmark_recommendation()

        warm_runs.append(latency)

        print(
            f"Run {i+1}: {latency:.2f} ms"
        )

    recommendation_stats = stats(
        warm_runs
    )

    # -------------------------------------------------------------

    print("\nConversation Benchmark\n")

    agent = InventoryAgent()

    conversation = benchmark_conversation(
        agent,
        state,
    )

    conversation_stats = stats(
        [
            c["latency_ms"]
            for c in conversation
        ]
    )

    # -------------------------------------------------------------

    summary = {
        "cold_recommendation_ms": round(
            cold,
            2,
        ),
        "recommendation": recommendation_stats,
        "conversation": conversation_stats,
    }

    # -------------------------------------------------------------
    # JSON
    # -------------------------------------------------------------

    with open(
        RESULTS_DIR / "benchmark_results.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "summary": summary,
                "conversation": conversation,
            },
            f,
            indent=4,
        )

    # -------------------------------------------------------------
    # CSV
    # -------------------------------------------------------------

    with open(
        RESULTS_DIR / "benchmark_results.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "Benchmark",
                "Latency (ms)",
            ]
        )

        writer.writerow(
            [
                "Cold Recommendation",
                round(cold, 2),
            ]
        )

        for i, value in enumerate(
            warm_runs,
            1,
        ):

            writer.writerow(
                [
                    f"Warm Recommendation {i}",
                    round(value, 2),
                ]
            )

        for row in conversation:

            writer.writerow(
                [
                    row["question"],
                    row["latency_ms"],
                ]
            )

    # -------------------------------------------------------------

    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"Cold Recommendation : {cold:.2f} ms"
    )

    print()

    print("Recommendation")

    for k, v in recommendation_stats.items():

        print(f"{k:15}: {v}")

    print()

    print("Conversation")

    for k, v in conversation_stats.items():

        print(f"{k:15}: {v}")

    print()

    print(
        "JSON:",
        RESULTS_DIR / "benchmark_results.json",
    )

    print(
        "CSV :",
        RESULTS_DIR / "benchmark_results.csv",
    )


if __name__ == "__main__":
    main()