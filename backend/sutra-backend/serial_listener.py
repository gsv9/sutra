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


def normalize_arduino_event(raw_event: dict) -> dict:
    """
    Normalize edge-device packets into the backend contract.
    """

    event_type = str(raw_event.get("event_type") or raw_event.get("event"), "NORMAL").upper()
    item_name = (
        raw_event.get("item")
        or raw_event.get("product")
        or raw_event.get("item_name")
        or "Rice"
    )

    current_weight = raw_event.get("current_weight")
    remaining_weight = raw_event.get("remaining_weight")
    weight_kg = raw_event.get("weight_kg")

    if remaining_weight is None:
        remaining_weight = (
            current_weight
            if current_weight is not None
            else weight_kg
            if weight_kg is not None
            else 0
        )

    if current_weight is None:
        current_weight = remaining_weight

    confidence = raw_event.get("confidence", 95)
    try:
        confidence = float(confidence)
        if confidence <= 1:
            confidence *= 100
        confidence = round(confidence)
    except Exception:
        confidence = 95

    return {
        "device_id": raw_event.get("device_id", "UNOQ-01"),
        "event": event_type,
        "item": item_name,
        "product": item_name,
        "remaining_weight": remaining_weight,
        "current_weight": current_weight,
        "weight_kg": weight_kg if weight_kg is not None else remaining_weight,
        "previous_weight": raw_event.get("previous_weight"),
        "delta": raw_event.get("delta"),
        "confidence": confidence,
        "slot_id": raw_event.get("slot_id", 1),
        "timestamp": raw_event.get("timestamp", datetime.now().isoformat()),
    }




# ─── REAL ARDUINO LISTENER ──────────────────────────────────────────────

def real_arduino_stream():
    """
    Reads actual JSON events from Arduino UNO Q via USB.
    Arduino sends one JSON line per event.
    """
    import serial

    print(f"[ARDUINO] Connecting to {ARDUINO_PORT}...")

    try:
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD_RATE, timeout=1)
        print(f"[ARDUINO] Connected to {ARDUINO_PORT}")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()

                if line:
                    try:
                        event = normalize_arduino_event(json.loads(line))
                        print(f"[ARDUINO] Received: {event}")

                        if event.get("event") != "NORMAL":
                            if on_event_received:
                                on_event_received(event)

                    except json.JSONDecodeError:
                        print(f"[ARDUINO] Non-JSON message: {line}")

    except serial.SerialException as e:
        print(f"[ARDUINO] Connection error: {e}")
        print("[ARDUINO] Check that Arduino is connected and port is correct")


# ─── MAIN FUNCTION: START LISTENING ─────────────────────────────────────

def start_listening(event_handler):
    """
    Starts the serial listener in a background thread.
    event_handler = function to call when event is received
    Called by main.py when server starts.
    """
    global on_event_received
    on_event_received = event_handler

    if USE_REAL_ARDUINO:
        target = real_arduino_stream
        print("[SERIAL] Starting REAL Arduino listener")
    else:
        target = mock_arduino_stream
        print("[SERIAL] Starting MOCK Arduino simulator")

    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    return thread
