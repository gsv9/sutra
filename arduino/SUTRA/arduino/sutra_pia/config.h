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
const float STABLE_THRESHOLD = 5.0;

// Need 10 stable readings before accepting
const int STABLE_COUNT = 10;

//====================================================
// Event Detection
//====================================================

// Ignore changes smaller than 10 grams
const float MIN_EVENT_CHANGE = 10.0;

#endif