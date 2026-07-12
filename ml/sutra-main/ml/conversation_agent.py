"""
Conversation Agent for the SUTRA AI Copilot.

Responsible for answering follow-up questions regarding an existing
recommendation. This agent never generates recommendations; it only
explains, compares and justifies previous decisions.
"""

from __future__ import annotations

import logging
from .agent import get_conversation_memory

from .conversation_memory import ConversationMemory
from .llm.factory import get_llm
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ConversationAgent:
    """
    Handles explainability and follow-up conversations.

    Uses:
        - Previous Recommendation
        - Business Context
        - Conversation History
        - Phi-3 Mini
    """

    def __init__(
        self,
        memory: ConversationMemory,
    ) -> None:

        self._memory = memory
        self._llm = get_llm()
        self._prompt_builder = PromptBuilder()

    # ---------------------------------------------------------

    def answer(
        self,
        question: str,
    ) -> str:
        """
        Generate a natural language response for a user question.
        """

        if (
            self._memory.context is None
            or self._memory.recommendation is None
        ):
            raise RuntimeError(
                "Conversation requested before a recommendation "
                "has been generated."
            )

        prompt = self._prompt_builder.build_conversation_prompt(
            question=question,
            context=self._memory.context,
            state=self._memory.recommendation,
        )

        logger.info("Generating conversational response.")

        answer = self._llm.generate(
            prompt=prompt,
            max_new_tokens=256,
            temperature=0.2,
        )

        self._memory.add_exchange(
            question=question,
            answer=answer,
        )

        logger.info("Conversation response generated.")

        return answer.strip()