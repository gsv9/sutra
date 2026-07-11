# serial_listener.py
# Listens to Arduino UNO Q via USB serial port
# Before July 11: uses mock simulator
# After July 11: reads real Arduino serial port

import json
import time
import threading
import random
from datetime import datetime
from config import USE_REAL_ARDUINO, ARDUINO_PORT, ARDUINO_BAUD_RATE

# This will be set by main.py when server starts
# It points to agent_bridge's trigger function
on_event_received = None


# ─── MOCK SIMULATOR ───────────────────────────────────────────
# Simulates what Arduino UNO Q would send
# Remove this on July 11 when real Arduino is connected

def mock_arduino_stream():
    """
    Generates fake Arduino events for testing.
    Sends a consumption_spike every 30 seconds.
    """
    print("[MOCK ARDUINO] Simulator started")

    # Wait 5 seconds before first event
    # Gives server time to fully start
    time.sleep(5)

    while True:
        # Simulate a consumption spike on Rice
        event = {
            "event": "consumption_spike",
            "item": "Rice",
            "remaining_weight": round(random.uniform(2.0, 4.5), 1),
            "confidence": random.randint(92, 99),
            "timestamp": datetime.now().isoformat()
        }

        print(f"[MOCK ARDUINO] Sending event: {event}")

        # Call the handler if it's been set
        if on_event_received:
            on_event_received(event)

        # Wait 30 seconds before next event
        # Change to 10 seconds for faster testing
        time.sleep(30)


# ─── REAL ARDUINO LISTENER ────────────────────────────────────
# This runs on July 11 when USE_REAL_ARDUINO = True

def real_arduino_stream():
    """
    Reads actual JSON events from Arduino UNO Q via USB.
    Arduino sends one JSON line per event.
    """
    import serial

    print(f"[ARDUINO] Connecting to {ARDUINO_PORT}...")

    try:
        # Open serial connection to Arduino
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD_RATE, timeout=1)
        print(f"[ARDUINO] Connected to {ARDUINO_PORT}")

        while True:
            # Read one line from Arduino
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()

                if line:
                    try:
                        # Parse the JSON Arduino sent
                        event = json.loads(line)
                        print(f"[ARDUINO] Received: {event}")

                        # Only trigger agent for actionable events
                        if event.get("event") != "normal":
                            if on_event_received:
                                on_event_received(event)

                    except json.JSONDecodeError:
                        # Arduino sometimes sends debug messages
                        # that aren't JSON — ignore them
                        print(f"[ARDUINO] Non-JSON message: {line}")

    except serial.SerialException as e:
        print(f"[ARDUINO] Connection error: {e}")
        print("[ARDUINO] Check that Arduino is connected and port is correct")


# ─── MAIN FUNCTION: START LISTENING ───────────────────────────

def start_listening(event_handler):
    """
    Starts the serial listener in a background thread.
    event_handler = function to call when event is received
    Called by main.py when server starts.
    """
    global on_event_received
    on_event_received = event_handler

    # Choose mock or real based on config flag
    if USE_REAL_ARDUINO:
        target = real_arduino_stream
        print("[SERIAL] Starting REAL Arduino listener")
    else:
        target = mock_arduino_stream
        print("[SERIAL] Starting MOCK Arduino simulator")

    # Run in background thread so it doesn't block the server
    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    return thread