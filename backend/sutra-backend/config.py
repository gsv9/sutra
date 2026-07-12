"""
Central configuration for the SUTRA backend.

Defaults are tuned for the local hackathon demo:
- real Phi-3 / Qualcomm NPU path enabled
- cloud disabled
- Arduino can be toggled on when the board is plugged in
"""

from __future__ import annotations

import os
from pathlib import Path

# ─── HARDWARE FLAGS ───────────────────────────────────────────
USE_REAL_ARDUINO = True

USE_REAL_AI = os.getenv("SUTRA_USE_REAL_AI", "true").lower() == "true"

USE_REAL_CLOUD = os.getenv("SUTRA_USE_REAL_CLOUD", "false").lower() == "true"

# ─── ARDUINO SETTINGS ─────────────────────────────────────────
# Change COM3 to your actual port when the board is connected
ARDUINO_PORT = r"\\.\COM13"
ARDUINO_BAUD_RATE = 115200

# ─── DATABASE SETTINGS ────────────────────────────────────────
# This creates a file called sutra.db in your project folder
DATABASE_URL = "sqlite:///./sutra.db"

# ─── SERVER SETTINGS ──────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000

# ─── BUSINESS SETTINGS ────────────────────────────────────────
# How many days of sales history to send to AI for reasoning
SALES_HISTORY_DAYS = 30

# ─── CLOUD SETTINGS ───────────────────────────────────────────
# These will be filled on July 11 when Qualcomm provides credentials
CLOUD_100_URL = "https://cloud100.qualcomm.com/api"
CLOUD_100_API_KEY = "your-api-key-here"

# Location of the authoritative ML project root.
# This should point at the folder that contains `ml/` and `models/`.
ML_PROJECT_ROOT = Path(
    os.getenv(
        "SUTRA_ML_ROOT",
        r"C:\Users\qcwor\Documents\Codex\2026-07-11\ok\sutra_full\source\ml\sutra-main",
    )
)
