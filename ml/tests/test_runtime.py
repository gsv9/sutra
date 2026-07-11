"""
Runtime smoke test for the SUTRA AI pipeline.

Run:

python -m ml.tests.test_runtime
"""

from ml.feature_engineering import FeatureEngineer
from ml.llm.factory import get_llm
from ml.prompt_builder import PromptBuilder
from ml.schemas import BusinessContext


def main():

    context = BusinessContext.model_validate(
        {
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
                }
            ],
            "upcoming_festivals": [],
            "timestamp": "2026-07-11T11:34:01",
        }
    )

    print("✓ BusinessContext")

    features = FeatureEngineer.compute(context)
    print("✓ Feature Engineering")

    builder = PromptBuilder()
    prompt, state = builder.build_recommendation_prompt(context)
    print("✓ Prompt Builder")

    llm = get_llm()
    print(f"✓ LLM Loaded : {llm.__class__.__name__}")

    print("\nPrompt Preview\n")
    print(prompt[:700])


if __name__ == "__main__":
    main()