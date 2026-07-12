#ifndef CONFIG_H
#define CONFIG_H

//====================================================
// Device
//====================================================

const char DEVICE_ID[] = "UNOQ-01";

//====================================================
// Serial
//====================================================

const long BAUD_RATE = 115200;

//====================================================
// HX711 Pins
//====================================================

const int HX711_DOUT = 3;
const int HX711_SCK  = 2;

//====================================================
// Calibration
//====================================================

// Replace ONLY if you recalibrate
const float CALIBRATION_FACTOR = -384.515015;

//====================================================
// Sampling
//====================================================

// Sensor polling interval (ms)
const unsigned long SAMPLE_INTERVAL_MS = 100;

//====================================================
// Stable Reading Detection
//====================================================

// Reading considered stable within ±5 grams
const float STABLE_THRESHOLD = 0.05;

// Need 10 stable readings before accepting
const int STABLE_COUNT = 10;

//====================================================
// Event Detection
//====================================================

// Ignore changes smaller than this sensor unit range
const float MIN_EVENT_CHANGE = 0.05;

// Thresholds use the same unit as LoadCell.getData().
// Live readings show placed weight around 0.7-1.1 and empty noise near 0.0.
const float OUT_OF_STOCK_THRESHOLD = 0.05;
const float LOW_STOCK_THRESHOLD = 0.30;
const float ITEM_ADDED_DELTA = 0.20;
const float BULK_PURCHASE_DELTA = 1.20;
const float CONSUMPTION_SPIKE_DELTA = -0.50;

// Variance above this level means the shelf is unstable or being tampered with
const float TAMPER_VARIANCE_THRESHOLD = 0.10;

#endif
