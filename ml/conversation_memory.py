"""
Conversation memory for the SUTRA AI Copilot.

Stores the latest recommendation and recent interactions so that
follow-up questions can be answered consistently without rebuilding
the entire reasoning process.
"""

from __future__ import annotations

from collections import deque

from .schemas import (
    BusinessContext,
    Recommendation,
)


class ConversationMemory:
    """
    Lightweight in-memory conversation store.
    """

    def __init__(self, max_history: int = 10) -> None:

        self._recommendation: Recommendation | None = None
        self._context: BusinessContext | None = None
        self._history = deque(maxlen=max_history)

    # ---------------------------------------------------------

    def update(
        self,
        recommendation: Recommendation,
        context: BusinessContext,
    ) -> None:

        self._recommendation = recommendation
        self._context = context

    # ---------------------------------------------------------

    def add_exchange(
        self,
        question: str,
        answer: str,
    ) -> None:

        self._history.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    # ---------------------------------------------------------

    @property
    def recommendation(self) -> Recommendation | None:
        return self._recommendation

    @property
    def context(self) -> BusinessContext | None:
        return self._context

    @property
    def history(self):

        return list(self._history)