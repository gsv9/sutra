from pathlib import Path

# ---------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------

LLM_BACKEND = "qualcomm"

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

CPU_DEVICE_MAP = "cpu"

LOG_LEVEL = "INFO"

# ---------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------

DEBUG_OUTPUT = True

# ---------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------

MAX_NEW_TOKENS = 256

TEMPERATURE = 0.0

TOP_P = 0.9

USE_CACHE = True

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

PROMPT_DIRECTORY = PROJECT_ROOT / "prompts"

TEST_DIRECTORY = PROJECT_ROOT / "tests"
