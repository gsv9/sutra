/*
====================================================
SUTRA Physical Intelligence Agent
Arduino UNO Q + HX711

Role:
HX711 Sensor Reading
        |
        v
Moving Average + Variance + Stability
        |
        v
Local Event Classification
        |
        v
JSON Serial Stream
====================================================
*/

#include <HX711_ADC.h>

#include "config.h"
#include "event_types.h"
#include "inventory.h"
#include "json_utils.h"

HX711_ADC LoadCell(
    HX711_DOUT,
    HX711_SCK
);

InventorySlot riceSlot = {
    1,
    "Rice",
    0.0,
    0.0
};

float sampleWindow[STABLE_COUNT];
int sampleIndex = 0;
int sampleCount = 0;
int stableReadings = 0;
float lastAverage = 0.0;
bool hasStableWeight = false;

float calculateAverage()
{
    float sum = 0.0;

    for(int i = 0; i < sampleCount; i++)
    {
        sum += sampleWindow[i];
    }

    if(sampleCount == 0)
    {
        return 0.0;
    }

    return sum / sampleCount;
}

float calculateVariance(float average)
{
    float sum = 0.0;

    for(int i = 0; i < sampleCount; i++)
    {
        float diff = sampleWindow[i] - average;
        sum += diff * diff;
    }

    if(sampleCount == 0)
    {
        return 0.0;
    }

    return sum / sampleCount;
}

void addSample(float weight)
{
    sampleWindow[sampleIndex] = weight;
    sampleIndex = (sampleIndex + 1) % STABLE_COUNT;

    if(sampleCount < STABLE_COUNT)
    {
        sampleCount++;
    }
}

EventType classifyInventoryEvent(float previousWeight, float currentWeight, float variance)
{
    float delta = currentWeight - previousWeight;

    if(variance >= TAMPER_VARIANCE_THRESHOLD)
    {
        return TAMPER_ALERT;
    }

    if(delta >= BULK_PURCHASE_DELTA)
    {
        return BULK_PURCHASE;
    }

    if(delta >= ITEM_ADDED_DELTA)
    {
        return ITEM_ADDED;
    }

    if(delta <= CONSUMPTION_SPIKE_DELTA)
    {
        return CONSUMPTION_SPIKE;
    }

    if(currentWeight <= OUT_OF_STOCK_THRESHOLD)
    {
        return OUT_OF_STOCK;
    }

    if(currentWeight <= LOW_STOCK_THRESHOLD)
    {
        return LOW_STOCK;
    }

    return NORMAL;
}

bool isMeaningfulEvent(EventType event, float delta)
{
    if(event != NORMAL)
    {
        return true;
    }

    return abs(delta) >= MIN_EVENT_CHANGE;
}

void setup()
{
    Serial.begin(BAUD_RATE);

    delay(500);

    LoadCell.begin();

    bool tare = true;

    LoadCell.start(
        2000,
        tare
    );

    if(
        LoadCell.getTareTimeoutFlag()
        ||
        LoadCell.getSignalTimeoutFlag()
    )
    {
        while(1);
    }

    LoadCell.setCalFactor(
        CALIBRATION_FACTOR
    );

    while(
        !LoadCell.update()
    );
}

void loop()
{
    if(
        !LoadCell.update()
    )
    {
        return;
    }

    float weight =
        LoadCell.getData();

    if(weight < 0)
    {
        weight = 0;
    }

    addSample(weight);

    if(sampleCount < STABLE_COUNT)
    {
        delay(
            SAMPLE_INTERVAL_MS
        );
        return;
    }

    float average = calculateAverage();
    float variance = calculateVariance(average);

    if(abs(average - lastAverage) <= STABLE_THRESHOLD)
    {
        stableReadings++;
    }
    else
    {
        stableReadings = 0;
    }

    lastAverage = average;

    if(stableReadings < STABLE_COUNT)
    {
        delay(
            SAMPLE_INTERVAL_MS
        );
        return;
    }

    if(!hasStableWeight)
    {
        riceSlot.previousWeightKg = average;
        riceSlot.currentWeightKg = average;
        hasStableWeight = true;

        delay(
            SAMPLE_INTERVAL_MS
        );
        return;
    }

    riceSlot.previousWeightKg = riceSlot.currentWeightKg;
    riceSlot.currentWeightKg = average;

    EventType event = classifyInventoryEvent(
        riceSlot.previousWeightKg,
        riceSlot.currentWeightKg,
        variance
    );

    float delta = riceSlot.currentWeightKg - riceSlot.previousWeightKg;

    if(isMeaningfulEvent(event, delta))
    {
        sendInventoryJSON(
            riceSlot,
            event
        );
    }

    stableReadings = 0;

    delay(
        SAMPLE_INTERVAL_MS
    );
}
