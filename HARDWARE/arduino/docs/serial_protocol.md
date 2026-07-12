# SUTRA Physical Intelligence Agent

## Serial Communication Protocol v1.0

Each JSON packet contains:

- device_id
- event
- product
- weight_kg
- confidence
- timestamp

Allowed Events:

- NORMAL
- CONSUMPTION_SPIKE
- BULK_PURCHASE
- TAMPER_ALERT
- SENSOR_HEALTH_ALERT