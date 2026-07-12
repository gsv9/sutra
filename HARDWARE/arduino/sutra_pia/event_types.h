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
    BULK_PURCHASE ,

    // Customer purchased many items
    CONSUMPTION_SPIKE,

    // Inventory Status
    LOW_STOCK,
    OUT_OF_STOCK,

    // Hardware
    SENSOR_ERROR,
    TAMPER_ALERT
};

#endif