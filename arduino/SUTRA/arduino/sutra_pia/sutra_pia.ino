/*
====================================================
SUTRA Physical Intelligence Agent
Arduino UNO Q + HX711
====================================================
*/

#include <HX711_ADC.h>

#include "config.h"
#include "inventory.h"
#include "event_types.h"
#include "event_utils.h"
#include "json_utils.h"

HX711_ADC LoadCell(HX711_DOUT, HX711_SCK);

//----------------------------------------------------
// Demo Inventory
//----------------------------------------------------

InventorySlot shelf =
{
    1,
    "Rice",
    0.0,
    0.0
};

//----------------------------------------------------

float lastReading = 0.0;
int stableCounter = 0;

//----------------------------------------------------
// Event Detection
//----------------------------------------------------

EventType detectEvent(float previousWeight, float currentWeight)
{
    float delta = currentWeight - previousWeight;

    // Protect against sensor drift
    if(previousWeight < 0) previousWeight = 0;
    if(currentWeight < 0) currentWeight = 0;

    delta = currentWeight - previousWeight;

    // Inventory Status
    if(currentWeight <= 5)
        return OUT_OF_STOCK;

    if(currentWeight <= 30)
        return LOW_STOCK;

    // Positive Changes
    if(delta >= 120)
        return CONSUMPTION_SPIKE;

    if(delta >= 20)
        return ITEM_ADDED;

    // Negative Changes
    if(delta <= -150)
        return LOSS_DETECTED;

    if(delta <= -80)
        return BULK_PURCHASE;

    if(delta <= -10)
        return NORMAL;

    return NORMAL;
}

//----------------------------------------------------
// Setup
//----------------------------------------------------

void setup()
{
    Serial.begin(BAUD_RATE);
    delay(100);

    LoadCell.begin();

    bool tare = true;

    LoadCell.start(2000, tare);

    if (LoadCell.getTareTimeoutFlag() ||
        LoadCell.getSignalTimeoutFlag())
    {
        while (1);
    }

    LoadCell.setCalFactor(CALIBRATION_FACTOR);

    while (!LoadCell.update());

    LoadCell.refreshDataSet();

    float initial = LoadCell.getData();

    if(initial < 0)
        initial = 0;

    shelf.previousWeightKg = initial;
    shelf.currentWeightKg = initial;

    lastReading = initial;
}

//----------------------------------------------------
// Main Loop
//----------------------------------------------------

void loop()
{
    if(!LoadCell.update())
        return;

    float current = LoadCell.getData();

    // Prevent negative values
    if(current < 0)
        current = 0;

    // Stable reading detection
    if(abs(current - lastReading) <= STABLE_THRESHOLD)
    {
        stableCounter++;
    }
    else
    {
        stableCounter = 0;
    }

    lastReading = current;

    if(stableCounter >= STABLE_COUNT)
    {
        stableCounter = 0;

        if(abs(current - shelf.currentWeightKg) >= MIN_EVENT_CHANGE)
        {
            shelf.previousWeightKg = shelf.currentWeightKg;
            shelf.currentWeightKg = current;

            EventType event = detectEvent(
                shelf.previousWeightKg,
                shelf.currentWeightKg
            );

            sendInventoryJSON(shelf, event);
        }
    }

    delay(SAMPLE_INTERVAL_MS);
}