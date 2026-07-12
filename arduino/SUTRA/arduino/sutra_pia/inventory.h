#ifndef INVENTORY_H
#define INVENTORY_H

struct InventorySlot
{
    uint8_t slotID;

    const char* productName;

    // Previous stable weight (grams)
    float previousWeightKg;

    // Current stable weight (grams)
    float currentWeightKg;
};

#endif