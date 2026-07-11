"""
Recommendation pipeline test.

Run:

python -m ml.tests.test_recommendation
"""

import json

from ml.agent import run_inference


def main():

    context = {
        "item": "Rice",
        "remaining_weight": 3.4,
        "reorder_threshold": 5.0,
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

    recommendation = run_inference(context)

    print("\nRecommendation\n")
    print(json.dumps(recommendation, indent=4))


if __name__ == "__main__":
    main()