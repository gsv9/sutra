# SUTRA Physical Intelligence Agent

## Serial Communication Protocol v1.0

Each JSON packet contains:

- device_id
- event
- product
- current_weight
- remaining_weight
- previous_weight
- delta
- confidence
- timestamp

Allowed Events:

- NORMAL
- ITEM_ADDED
- CONSUMPTION_SPIKE
- BULK_PURCHASE
- LOW_STOCK
- OUT_OF_STOCK
- TAMPER_ALERT
- SENSOR_ERROR

Notes:

- `product` is the canonical item field for the edge device.
- The backend also accepts `item` as a compatibility alias.
- `confidence` should be reported on a 0–100 scale if available.
- The backend normalizes `current_weight` / `remaining_weight` when one of them is missing.
