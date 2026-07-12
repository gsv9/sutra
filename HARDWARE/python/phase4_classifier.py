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

    # Rice added / refill
    if delta >= 1.20:
        return "BULK_PURCHASE", 0.98

    if delta >= 0.20:
        return "ITEM_ADDED", 0.96

    # Sudden high consumption
    if delta <= -0.50:
        return "CONSUMPTION_SPIKE", 0.99

    # Shelf empty
    if current_weight <= 0.05:
        return "OUT_OF_STOCK", 0.99

    # Shelf almost empty
    if current_weight <= 0.30:
        return "LOW_STOCK", 0.97

    # Normal customer purchase
    if delta <= -0.05:
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
        "previous_weight": 1.80,
        "current_weight": 0.20,
        "delta": -1.60,
        "event": "CONSUMPTION_SPIKE"
    }

    print(infer_event(sample))
