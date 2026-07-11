"""
Feature Engineering for the SUTRA AI Copilot.

This module derives deterministic business intelligence from the backend
BusinessContext before it is sent to Phi-3 Mini.

Responsibilities
----------------
- Inventory analytics
- Supplier analytics
- Festival analytics
- Sales trend analysis
- Business signal generation

No AI inference should occur here.
"""

from __future__ import annotations

from .schemas import BusinessContext, EngineeredContext


class FeatureEngineer:
    """
    Generates deterministic business intelligence from raw backend data.

    These engineered features are consumed by the PromptBuilder so that
    Phi-3 focuses on reasoning rather than arithmetic.
    """

    @staticmethod
    def compute(context: BusinessContext) -> EngineeredContext:
        """
        Compute deterministic business features.
        """

        if not context.suppliers:
            raise ValueError("BusinessContext must contain at least one supplier.")

        features: dict = {}

        # ==========================================================
        # Inventory Analytics
        # ==========================================================

        if context.avg_daily_sales > 0:
            days_until_stockout = (
                context.remaining_weight /
                context.avg_daily_sales
            )
        else:
            days_until_stockout = float("inf")

        features["days_until_stockout"] = round(days_until_stockout, 2)

        if context.remaining_weight <= 0:
            inventory_status = "OUT_OF_STOCK"

        elif context.remaining_weight < context.reorder_threshold:
            inventory_status = "CRITICAL"

        elif context.remaining_weight < context.reorder_threshold * 1.5:
            inventory_status = "LOW"

        else:
            inventory_status = "HEALTHY"

        features["inventory_status"] = inventory_status

        # ==========================================================
        # Sales Trend
        # ==========================================================

        trend = context.sales_trend

        if len(trend) >= 4:

            midpoint = len(trend) // 2

            first_avg = sum(trend[:midpoint]) / midpoint

            second_avg = sum(trend[midpoint:]) / (len(trend) - midpoint)

            if second_avg > first_avg * 1.05:
                sales_trend = "INCREASING"

            elif second_avg < first_avg * 0.95:
                sales_trend = "DECREASING"

            else:
                sales_trend = "STABLE"

        else:
            sales_trend = "UNKNOWN"

        features["sales_trend"] = sales_trend

        features["average_recent_sales"] = (
            round(sum(trend) / len(trend), 2)
            if trend else 0
        )

        # ==========================================================
        # Supplier Analytics
        # ==========================================================

        cheapest_supplier = min(
            context.suppliers,
            key=lambda supplier: supplier.price_per_unit,
        )

        fastest_supplier = min(
            context.suppliers,
            key=lambda supplier: supplier.lead_time_days,
        )

        most_reliable_supplier = max(
            context.suppliers,
            key=lambda supplier: supplier.reliability_score,
        )

        features["cheapest_supplier"] = cheapest_supplier.supplier_name
        features["fastest_supplier"] = fastest_supplier.supplier_name
        features["most_reliable_supplier"] = most_reliable_supplier.supplier_name

        # ==========================================================
        # Festival Analytics
        # ==========================================================

        if context.upcoming_festivals:

            nearest = min(
                context.upcoming_festivals,
                key=lambda festival: festival.days_away,
            )

            features["festival_near"] = True
            features["festival_name"] = nearest.name
            features["festival_days"] = nearest.days_away

            if nearest.days_away <= 3:
                features["festival_risk"] = "HIGH"

            elif nearest.days_away <= 7:
                features["festival_risk"] = "MEDIUM"

            else:
                features["festival_risk"] = "LOW"

        else:

            features["festival_near"] = False
            features["festival_name"] = None
            features["festival_days"] = None
            features["festival_risk"] = "NONE"

        # ==========================================================
        # Business Signals
        # ==========================================================

        signals: list[str] = []

        if inventory_status == "OUT_OF_STOCK":
            signals.append(
                "Inventory is exhausted. Immediate replenishment is required."
            )

        elif inventory_status == "CRITICAL":
            signals.append(
                "Inventory is below the configured reorder threshold."
            )

        if days_until_stockout < 2:
            signals.append(
                "Current inventory is expected to be depleted within two days."
            )

        if sales_trend == "INCREASING":
            signals.append(
                "Recent sales indicate increasing customer demand."
            )

        elif sales_trend == "DECREASING":
            signals.append(
                "Recent sales indicate decreasing customer demand."
            )

        if features["festival_near"]:
            signals.append(
                f"Upcoming festival '{features['festival_name']}' in "
                f"{features['festival_days']} day(s) may increase demand."
            )

        if (
            cheapest_supplier.supplier_name
            != most_reliable_supplier.supplier_name
        ):
            signals.append(
                "The cheapest supplier is not the most reliable supplier."
            )

        if fastest_supplier.lead_time_days > days_until_stockout:
            signals.append(
                "Supplier lead time exceeds estimated stock availability."
            )

        signals.append(
            f"Recommended supplier should balance price, reliability and delivery speed."
        )

        features["business_signals"] = signals

        return EngineeredContext(**features)