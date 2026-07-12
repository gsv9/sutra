#ifndef EVENT_UTILS_H
#define EVENT_UTILS_H

#include "event_types.h"

const char* eventToString(EventType event)
{
    switch(event)
    {
        case NORMAL:
            return "NORMAL";

        case ITEM_ADDED:
            return "ITEM_ADDED";

        case ITEM_REMOVED:
            return "ITEM_REMOVED";

        case LOSS_DETECTED:
            return "LOSS_DETECTED";

        case CONSUMPTION_SPIKE:
            return "CONSUMPTION_SPIKE";

        case BULK_PURCHASE:
            return "BULK_PURCHASE";

        case LOW_STOCK:
            return "LOW_STOCK";

        case OUT_OF_STOCK:
            return "OUT_OF_STOCK";

        case SENSOR_ERROR:
            return "SENSOR_ERROR";

        case TAMPER_ALERT:
            return "TAMPER_ALERT";

        default:
            return "UNKNOWN";
    }
}

#endif