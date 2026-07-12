"""
Prompt Builder for the SUTRA AI Copilot.

Responsible only for converting structured business data into
high-quality prompts for Microsoft Phi-3.

No business calculations occur here.
"""

from __future__ import annotations

import json

from . import config
from .feature_engineering import FeatureEngineer
from .schemas import (
    AgentState,
    BusinessContext,
    Recommendation,
)


class PromptBuilder:

    def __init__(self):

        prompt_dir = config.PROMPT_DIRECTORY

        self.recommendation_system = (
            prompt_dir / "recommendation_system.txt"
        ).read_text(encoding="utf-8")

        self.conversation_system = (
            prompt_dir / "conversation_system.txt"
        ).read_text(encoding="utf-8")

    # -------------------------------------------------------------

    @staticmethod
    def _supplier_summary(context: BusinessContext) -> str:

        lines = []

        for supplier in context.suppliers:

            lines.append(
                f"""
Supplier : {supplier.supplier_name}
Price : {supplier.price_per_unit}
Reliability : {supplier.reliability_score}%
Lead Time : {supplier.lead_time_days} day(s)
""".strip()
            )

        return "\n\n".join(lines)

    # -------------------------------------------------------------

    @staticmethod
    def _business_signals(state: AgentState) -> str:

        if not state.engineered_context.business_signals:
            return "No special business signals."

        return "\n".join(
            f"• {signal}"
            for signal in state.engineered_context.business_signals
        )

    # -------------------------------------------------------------

    def build_recommendation_prompt(
        self,
        context: BusinessContext,
    ) -> tuple[str, str, AgentState]:

        engineered = FeatureEngineer.compute(context)

        state = AgentState(
            recommendation=Recommendation(
                recommendation="",
                supplier="",
                quantity=0,
                unit_price=0,
                total_cost=0,
                savings=0,
                reasoning="",
                confidence=0,
                expected_delivery_days=0,
            ),
            engineered_context=engineered,
        )

        user_prompt = f"""
==================================================
ITEM
==================================================

{context.item}

==================================================
CURRENT INVENTORY
==================================================

Remaining Stock : {context.remaining_weight} {context.unit}

Reorder Threshold : {context.reorder_threshold}

Average Daily Sales : {context.avg_daily_sales}

Estimated Stockout : {engineered.days_until_stockout:.2f} day(s)

Inventory Status : {engineered.inventory_status}

Sales Trend : {engineered.sales_trend}

==================================================
FESTIVAL
==================================================

Festival Nearby : {engineered.festival_near}

Festival Name : {engineered.festival_name}

Festival Risk : {engineered.festival_risk}

==================================================
SUPPLIERS
==================================================

{self._supplier_summary(context)}

==================================================
BUSINESS SIGNALS
==================================================

{self._business_signals(state)}

==================================================
TASK
==================================================

Analyse the inventory situation using ONLY the supplied business context.

Prioritise:

1. Prevent stockouts.
2. Maintain business continuity.
3. Consider upcoming demand spikes.
4. Balance supplier reliability against procurement cost.
5. Avoid unnecessary inventory holding.

Never fabricate suppliers.

Never fabricate inventory information.

Return ONLY ONE valid JSON object.

The JSON MUST exactly match this schema:

{{
  "recommendation": "Order Now | Monitor | No Action",
  "supplier": "Supplier Name",
  "quantity": 0,
  "unit_price": 0,
  "total_cost": 0,
  "savings": 0,
  "reasoning": "Short explanation",
  "confidence": 95,
  "expected_delivery_days": 0
}}

Rules:

- Output ONLY JSON.
- No markdown.
- No ``` blocks.
- No explanation before or after the JSON.
"""

        return (
            self.recommendation_system,
            user_prompt.strip(),
            state,
        )

    # -------------------------------------------------------------

    def build_conversation_prompt(
        self,
        question: str,
        context: BusinessContext,
        recommendation: Recommendation,
    ) -> tuple[str, str]:

        recommendation_json = json.dumps(
            recommendation.model_dump(mode="json"),
            indent=2,
        )

        user_prompt = f"""
==================================================
PREVIOUS RECOMMENDATION
==================================================

{recommendation_json}

==================================================
CURRENT BUSINESS CONTEXT
==================================================

{json.dumps(
    context.model_dump(mode="json"),
    indent=2
)}

==================================================
QUESTION
==================================================

{question}

Answer naturally.

Be concise.

Never contradict the previous recommendation unless
the supplied business context clearly indicates that
the recommendation would now be different.

Explain your reasoning clearly.
"""

        return (
            self.conversation_system,
            user_prompt.strip(),
        )