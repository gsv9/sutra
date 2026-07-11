"""
Conversation pipeline test.

Run:

python -m ml.tests.test_conversation
"""

from ml.agent import InventoryAgent

QUESTIONS = [
    "Why reorder now?",
    "Why ABC Traders?",
    "Compare suppliers.",
    "Can I wait two days?",
    "What if festival is cancelled?",
    "How confident are you?",
]


def main():

    context = {
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

    agent = InventoryAgent()

    from ml.agent import run_inference

    state = run_inference(
            context,
             return_state=True,
        )

    for question in QUESTIONS:

        print("=" * 80)
        print("USER :", question)

        answer = agent.chat(
            question,
            state,
            state.recommendation,
        )

        print("\nAI :")
        print(answer)
        print()


if __name__ == "__main__":
    main()