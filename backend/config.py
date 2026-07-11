# config.py
# Central configuration for SUTRA backend
# Change these flags to switch between mock and real hardware

# ─── HARDWARE FLAGS ───────────────────────────────────────────
# Set to True on July 11 when real Arduino is connected
USE_REAL_ARDUINO = False

# Set to True on July 11 when Qualcomm AI Hub NPU is ready
USE_REAL_AI = False

# Set to True on July 11 when Cloud 100 credentials are available
USE_REAL_CLOUD = False

# ─── ARDUINO SETTINGS ─────────────────────────────────────────
# Change COM3 to your actual port on July 11
# Check Device Manager on Windows to find the right port
ARDUINO_PORT = "COM3"
ARDUINO_BAUD_RATE = 9600

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