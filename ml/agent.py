"""
Public AI interface for the SUTRA AI Copilot.

The backend should only import this module.

Public APIs
-----------
run_inference(context) -> dict
chat(question, state, context) -> str
"""

from __future__ import annotations

import logging
from .conversation_memory import ConversationMemory
from .explainer import Explainer
from .metrics import MetricsRecorder
from . import config

from .llm.factory import get_llm
from .parser import RecommendationParser
from .prompt_builder import PromptBuilder
from .schemas import (
    AgentState,
    BusinessContext,
)

logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    Coordinates the complete recommendation pipeline.

Responsibilities

- Validate backend payload
- Build business prompt
- Execute LLM inference
- Parse recommendation
- Store explainability
- Record runtime metrics
- Maintain conversation memory
    """

    def __init__(self) -> None:

        self._llm = get_llm()
        self._prompt_builder = PromptBuilder()
        self._memory = ConversationMemory()
        self._explainer = Explainer()
        self._metrics = MetricsRecorder()

    # ---------------------------------------------------------

    @staticmethod
    def _validate_context(
        context: dict | BusinessContext,
    ) -> BusinessContext:
        """
        Validate backend payload.
        """

        if isinstance(context, BusinessContext):
            return context

        return BusinessContext.model_validate(context)

    # ---------------------------------------------------------

    def run_inference(
        self,
        context: dict | BusinessContext,
    ) -> AgentState:
        """
        Execute the recommendation pipeline.

        Backend
            ↓
        BusinessContext
            ↓
        Feature Engineering
            ↓
        Prompt Builder
            ↓
        Phi-3
            ↓
        Parser
            ↓
        AgentState
        """

        context = self._validate_context(context)

        logger.info(
            "Generating recommendation for %s",
            context.item,
        )

        prompt, state = (
            self._prompt_builder.build_recommendation_prompt(
                context
            )
        )
        self._metrics.start()
        raw_response = self._llm.generate(
            prompt=prompt,
            max_new_tokens=256,
            temperature=0.0,
        )

        recommendation = RecommendationParser.parse(
            raw_response
        )
        self._memory.update(
           recommendation=recommendation,
           context=context,
        )

        self._explainer.update(
           recommendation=recommendation,
           engineered_context=state.engineered_context,
)

        metrics = self._metrics.stop(
         backend=config.LLM_BACKEND,
         prompt=prompt,
         response=raw_response,
         )

        logger.info(
         "Backend=%s | Latency=%.2f ms",
          metrics.backend,
        metrics.latency_ms,
        )

        state.recommendation = recommendation

        logger.info(
            "Recommendation generated successfully."
        )

        return state

    # ---------------------------------------------------------

    def chat(
        self,
        question: str,
        state: AgentState,
        context: dict | BusinessContext,
    ) -> str:
        """
        Answer follow-up questions regarding a recommendation.
        """

        context = self._validate_context(context)

        logger.info(
            "Conversation question received."
        )

        self._memory.update(
          recommendation=state.recommendation,
          context=context,
         )

        prompt = self._prompt_builder.build_conversation_prompt(
          question=question,
          context=context,
         recommendation=state.recommendation,
        )

        return self._llm.generate(
            prompt=prompt,
            max_new_tokens=384,
            temperature=0.2,
        )


# ---------------------------------------------------------------------
# Singleton Agent Instance
# ---------------------------------------------------------------------

_AGENT = InventoryAgent()


# ---------------------------------------------------------------------
# Public Backend API
# ---------------------------------------------------------------------

def run_inference(
    context: dict,
    return_state: bool = False,
):
    """
    Backend entry point.

    Parameters
    ----------
    context
        Backend payload.

    return_state
        False -> return backend JSON.

        True -> return AgentState for the conversation pipeline.
    """

    state = _AGENT.run_inference(context)

    if return_state:
        return state

    return state.recommendation.model_dump()


def chat(
    question: str,
    state: AgentState,
    context: dict | BusinessContext,
) -> str:
    """
    Public conversation API.
    """

    return _AGENT.chat(
        question=question,
        state=state,
        context=context,
    )

def get_conversation_memory() -> ConversationMemory:
    """
    Expose shared conversation memory.
    """

    return _AGENT._memory