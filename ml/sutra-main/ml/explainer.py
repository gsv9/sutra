"""
Explainability module for the SUTRA AI Copilot.

Stores structured reasoning behind every recommendation so that
follow-up questions can reuse deterministic business intelligence
before invoking the language model.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import Recommendation


@dataclass(slots=True)
class ExplanationRecord:
    """
    Stores explainability metadata for a recommendation.
    """

    recommendation: Recommendation

    inventory_status: str

    stockout_days: float

    business_signals: list[str]

    selected_supplier: str

    confidence: int


class Explainer:
    """
    Lightweight explainability store.
    """

    def __init__(self):

        self._record: ExplanationRecord | None = None

    # ---------------------------------------------------------

    def update(
        self,
        recommendation: Recommendation,
        engineered_context,
    ) -> None:

        self._record = ExplanationRecord(
            recommendation=recommendation,
            inventory_status=engineered_context.inventory_status,
            stockout_days=engineered_context.days_until_stockout,
            business_signals=engineered_context.business_signals,
            selected_supplier=recommendation.supplier,
            confidence=recommendation.confidence,
        )

    # ---------------------------------------------------------

    @property
    def record(self) -> ExplanationRecord | None:
        return self._record