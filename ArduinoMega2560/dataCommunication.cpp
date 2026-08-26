#include "dataCommunication.h"
#include "dataManagement.h"

extern SystemData currentData;

unsigned long lastPiHeartbeat = 0;
bool piConnectedStatus = false;

void initCommunication(){
    Serial.begin(115200);
    if (!SD.begin(SD_CHIP_SELECT)) {
        Serial.println(F("SD card failed or not present"))
    }
}

void processPiCommands(){
    while (Serial.available() > 0) {
        char cmd = Serial.read();
        // Both 'H' (Heartbeat) and 'S' (Sample) prove the Pi is alive
        if (cmd == 'H' || cmd == 'S'){
            lastPiHeartbeat = millis();
            piConnectedStatus = true;
        }
        //If the Pi explicitely asks for a sample, gather and send it immediately
        if (cmd == 'S'){
            processAndRouteData(currentData);
        }
    }
    if (millis() - lastPiHeartbeat > PI_TIMEOUT) {
        piConnectedStatus = false;
    }
}

bool isPiConnected(){
    return piConnectedStatus;
}

void sendDataToPi(JsonDocument& doc){
    serializeJson(doc, Serial);
    Serial.println();
}

void saveDataToSD(JsonDocument& doc){
    File dataFile = SD.open("data.txt", FILE_WRITE);
    if (dataFile){
        serializeJson(doc, dataFile);
        dataFile.println() // Newline delimited JSON
        dataFile.close()
    }
}