#ifndef EVENT_TYPES_H
#define EVENT_TYPES_H

enum EventType
{
    // Normal customer purchase
    NORMAL,

    // Small shelf refill
    ITEM_ADDED,

    // Reserved for future
    ITEM_REMOVED,

    // Sudden unexplained inventory loss
    LOSS_DETECTED,

    // Major shelf restock
    CONSUMPTION_SPIKE,

    // Customer purchased many items
    BULK_PURCHASE,

    // Inventory Status
    LOW_STOCK,
    OUT_OF_STOCK,

    // Hardware
    SENSOR_ERROR,
    TAMPER_ALERT
};

#endif