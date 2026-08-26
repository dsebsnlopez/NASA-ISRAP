#ifndef SENSORS_H
#define SENSORS_H

#include "config.h"

// GNSS Functions
void initGNSS();
void processGNSSConnection();
bool isGNSSCommunicating();
bool logLocationData(GPSData &data);
bool logTimeData(GPSData &data);

// Gas Sensor Functions
void initGasSensors();
float readNO2();
float readO3();
bool NO2Connected();
bool O3Connected();

#endif