#include "config.h"
#include "sensors.h" 
#include "dataManagement.h"
#include "dataCommunication.h"

unsigned long lastReadTime = 0;
SystemData currentData;

void setup(){
    Wire.begin();
    initCommunication();
    initSensors();
    initGNSS();
}

void loop(){
// 1. Monitor Connectiosn
    processGNSSConnection();
    processPiCommands();
}