"""
Parser for Phi-3 Mini recommendation responses.

Responsibilities
----------------
- Extract JSON from raw model output.
- Validate using Pydantic.
- Attempt lightweight recovery from common formatting mistakes.
"""

from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from .schemas import Recommendation

logger = logging.getLogger(__name__)


class ResponseParsingError(Exception):
    """Raised when the recommendation cannot be parsed."""


class RecommendationParser:
    """
    Parses and validates Phi-3 recommendation responses.
    """

    @staticmethod
    def parse(raw_output: str) -> Recommendation:
        """
        Parse a Recommendation from raw Phi-3 output.
        """

        cleaned = RecommendationParser._extract_json(raw_output)

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as exc:

            logger.warning(
                "Initial JSON parsing failed (%s). Attempting repair...",
                exc,
            )

            cleaned = RecommendationParser._repair_json(cleaned)

            try:
                data = json.loads(cleaned)

            except json.JSONDecodeError as exc:
                raise ResponseParsingError(
                    f"Unable to decode JSON.\n\n{raw_output}"
                ) from exc

        try:
            return Recommendation.model_validate(data)

        except ValidationError as exc:
            raise ResponseParsingError(
                f"Recommendation schema validation failed.\n\n{exc}"
            ) from exc

    # ---------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract the first JSON object from model output.
        """

        text = text.strip()
        text = text.replace("\r", "")

        text = text.replace("```json", "")
        text = text.replace("```", "")

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ResponseParsingError(
                "No JSON object found in model output."
            )

        return match.group(0)

    # ---------------------------------------------------------

    @staticmethod
    def _repair_json(text: str) -> str:
        """
        Perform lightweight JSON repair.

        This intentionally avoids changing business content.
        """

        repaired = text

        repaired = repaired.replace("\r", "")
        repaired = repaired.replace("\n", " ")

        repaired = re.sub(r"\s+", " ", repaired)

        repaired = re.sub(r",\s*}", "}", repaired)
        repaired = re.sub(r",\s*]", "]", repaired)

        repaired = repaired.strip()

        return repaired