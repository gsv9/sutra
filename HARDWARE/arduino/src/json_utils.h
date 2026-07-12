#ifndef JSON_UTILS_H
#define JSON_UTILS_H

#include "config.h"
#include "inventory.h"
#include "event_utils.h"

void sendInventoryJSON(const InventorySlot &slot, EventType event)
{
    float delta = slot.currentWeightKg - slot.previousWeightKg;

    Serial.print("{");

    Serial.print("\"device_id\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",");

    Serial.print("\"timestamp\":");
    Serial.print(millis());
    Serial.print(",");

    Serial.print("\"slot_id\":");
    Serial.print(slot.slotID);
    Serial.print(",");

    Serial.print("\"product\":\"");
    Serial.print(slot.productName);
    Serial.print("\",");

    Serial.print("\"previous_weight\":");
    Serial.print(slot.previousWeightKg, 2);
    Serial.print(",");

    Serial.print("\"current_weight\":");
    Serial.print(slot.currentWeightKg, 2);
    Serial.print(",");

    Serial.print("\"delta\":");
    Serial.print(delta, 2);
    Serial.print(",");

    Serial.print("\"event\":\"");
    Serial.print(eventToString(event));
    Serial.print("\"");

    Serial.println("}");
}

#endif