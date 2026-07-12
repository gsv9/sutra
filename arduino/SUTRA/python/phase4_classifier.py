"""
=========================================================
SUTRA
Phase 4 - AI Event Classification
=========================================================
"""

def classify_event(previous_weight, current_weight):

    previous_weight = max(previous_weight, 0)
    current_weight = max(current_weight, 0)

    delta = current_weight - previous_weight

    # Shelf empty
    if current_weight <= 5:
        return "OUT_OF_STOCK", 0.99

    # Shelf almost empty
    if current_weight <= 30:
        return "LOW_STOCK", 0.97

    # Rice added / refill
    if delta >= 20:
        return "ITEM_ADDED", 0.96

    # Sudden high consumption
    if delta <= -120:
        return "CONSUMPTION_SPIKE", 0.99

    # Normal customer purchase
    if delta <= -10:
        return "NORMAL", 0.95

    return "NORMAL", 0.90


def infer_event(data):

    result = dict(data)

    event, confidence = classify_event(
        result["previous_weight"],
        result["current_weight"]
    )

    result["predicted_event"] = event
    result["confidence"] = confidence

    return result


# Test
if __name__ == "__main__":

    sample = {
        "device_id": "UNOQ-01",
        "timestamp": 12345,
        "slot_id": 1,
        "product": "Rice",
        "previous_weight": 180,
        "current_weight": 20,
        "delta": -160,
        "event": "CONSUMPTION_SPIKE"
    }

    print(infer_event(sample))
