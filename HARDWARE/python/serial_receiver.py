"""
=========================================================
SUTRA
Phase 4 - AI Serial Receiver
=========================================================
"""

import serial
import json
import time

from phase4_classifier import infer_event

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

PORT = r"\\.\COM13"
BAUD_RATE = 115200

print("======================================")
print(" SUTRA Phase 4 AI Engine")
print(" Waiting for Arduino...")
print("======================================")

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
except Exception as e:
    print("Unable to open serial port:", e)
    exit()

# Wait for Arduino reset
time.sleep(2)

# Remove startup garbage
ser.reset_input_buffer()

# ----------------------------------------------------
# Main Loop
# ----------------------------------------------------

while True:

    try:

        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        # Ignore non-JSON messages
        if not line.startswith("{"):
            continue

        data = json.loads(line)

        result = infer_event(data)

        print()
        print("======================================")
        print("          SUTRA AI OUTPUT")
        print("======================================")
        print(f"Device          : {result['device_id']}")
        print(f"Product         : {result['product']}")
        print("--------------------------------------")
        print(f"Previous Weight : {result['previous_weight']:.2f} g")
        print(f"Current Weight  : {result['current_weight']:.2f} g")
        print(f"Weight Change   : {result['delta']:.2f} g")
        print("--------------------------------------")
        print(f"Arduino Event   : {result['event']}")
        print(f"ML Event        : {result['predicted_event']}")
        print(f"Confidence      : {result['confidence']*100:.1f}%")
        print("======================================")

    except json.JSONDecodeError:
        continue

    except KeyboardInterrupt:
        print("\nStopping...")
        break

    except Exception as e:
        print("Error:", e)

ser.close()
