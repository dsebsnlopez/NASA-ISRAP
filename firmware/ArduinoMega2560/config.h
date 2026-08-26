#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <ArduinoJson.h>
#include <SparkFun_u-blox_GNSS_Arduino_Library.h>
#include "DFRobot_MultiGasSensor.h"

// --- Pins ---
const int SD_CHIP_SELECT = 53;

// --- Constants ---
const unsigned long PI_TIMEOUT = 1500;

// --- Shared Data Structures ---
struct GPSData {
    long latitude;
    long longitude;
    long altitude;
    byte SIV; // Satellites in View
    uint16_t year;
    uint8_t month;
    uint8_t day;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
};

struct SystemData {
    long latitude;
    long longitude;
    float no2_ppm;
    float o3_ppm;
};

#endif