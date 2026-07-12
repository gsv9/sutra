#ifndef EVENT_TYPES_H
#define EVENT_TYPES_H

enum EventType
{
    // No significant change
    NORMAL,

    // Small shelf refill
    ITEM_ADDED,

    // Reserved for future
    ITEM_REMOVED,

    // Large unexplained inventory loss
    LOSS_DETECTED,

    // Large shelf restock
    BULK_PURCHASE,

    // Sudden customer purchase
    CONSUMPTION_SPIKE,

    // Inventory Status
    LOW_STOCK,
    OUT_OF_STOCK,

    // Hardware
    SENSOR_ERROR,
    TAMPER_ALERT
};

#endif