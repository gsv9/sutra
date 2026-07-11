from pathlib import Path

# ---------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------

LLM_BACKEND = "hf"

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

CPU_DEVICE_MAP = "cpu"

LOG_LEVEL = "INFO"

# ---------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------

MAX_NEW_TOKENS = 64

TEMPERATURE = 0.0

TOP_P = 0.9

USE_CACHE = True

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

PROMPT_DIRECTORY = PROJECT_ROOT / "prompts"

TEST_DIRECTORY = PROJECT_ROOT / "tests"