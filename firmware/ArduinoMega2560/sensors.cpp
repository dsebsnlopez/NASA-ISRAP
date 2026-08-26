#include "sensors.h"

SFE_UBLOX_GNSS myGNSS;

// Connection Management 
enum GNSSState{
    STATE_DISCONNECTED, STATE_CONNECTING, STATE_CONNECTED};
GNSSState gpsState = STATE_DISCONNECTED;
unsigned long lastConnectAttempt = 0;
const unsigned long CONNECT_INTERVAL = 3000; // Reconnection every 3 seconds

// Non-Blocking GPS Initialization
void initGNSS(){
    gpsState = STATE_CONNECTING;
    lastConnectAttempt = 0;
}

void processGNSSConnection() {
    if (gpsState == STATE_CONNECTED) return;

    if (millis() - lastConnectAttempt >= CONNECT_INTERVAL) {
        lastConnectAttempt = millis();
        Serial.println(F("[GPS] Attempting non-blocking connection..."));

        // In v2, begin() accepts Wire and the I2C address directly.
        // It returns true immediately if the module is found.
        if (myGNSS.begin(Wire, 0x42) == true) { 
            Serial.println(F("[GPS] Connected successfully!"));
            
            // v2 specific method to disable NMEA and enable UBX binary over I2C
            myGNSS.setI2COutput(COM_TYPE_UBX); 
            myGNSS.saveConfiguration(); // Save settings to the module's RAM/BBR
            
            gpsState = STATE_CONNECTED;
        } else {
            Serial.println(F("[GPS] Module not responding. Will retry."));
        }
    }
}

// Helper GPS Functions
bool isGNSSCommunicating(void) {
    if (gpsState != STATE_CONNECTED) {
        return false;
    }
    
    // Quick hardware-level I2C ping to ensure the bus hasn't frozen
    Wire.beginTransmission(0x42);
    if (Wire.endTransmission() != 0) {
        Serial.println(F("[GPS] Warning: Connection lost during operation!"));
        gpsState = STATE_DISCONNECTED; 
        return false;
    }
    return true;
}

bool logLocationData(GPSData &data) {
    if (!isGNSSCommunicating()) return false;

    data.latitude = myGNSS.getLatitude();
    data.longitude = myGNSS.getLongitude();
    data.altitude = myGNSS.getAltitude();
    data.SIV = myGNSS.getSIV();
    
    return true;
}

bool logTimeData(GPSData &data) {
    if (!isGNSSCommunicating()) return false;

    data.year   = myGNSS.getYear();
    data.month  = myGNSS.getMonth();
    data.day    = myGNSS.getDay();
    data.hour   = myGNSS.getHour();
    data.minute = myGNSS.getMinute();
    data.second = myGNSS.getSecond();
    
    return true;
}

// Blocking Gas Sensor Intialization
#define NO2_address 0x74
#define O3_address 0x77
DFRobot_GAS_I2C gas_NO2(&Wire ,NO2_address);
DFRobot_GAS_I2C gas_O3(&Wire ,O3_address);


void initGasSensors(){
    int connectionCounter = 0;
    // NO2 sensor Initialize
    while(!gas_NO2.begin() && connectionCounter < 3){
        Serial.println(F("NO2 Sensor NOT found !"));
        delay(1000);
        connectionCounter++;
    }
    if (connectionCounter < 3){
        Serial.println(F("The NO2 sensor is connected successfully!"));
        gas_NO2.changeAcquireMode(gas_NO2.PASSIVITY);
        delay(1000);
        gas_NO2.setTempCompensation(gas_NO2.ON);
    }
    

    // O3 sensor Initialize
    connectionCounter = 0;
    while(!gas_O3.begin() && connectionCounter < 3){
        Serial.println("O3 Sensor NOT found !");
        delay(1000);
        connectionCounter++;
    }
    if(connectionCounter 3){
        Serial.println("The O3 sensor is connected successfully!");
        gas_O3.changeAcquireMode(gas_O3.PASSIVITY);
        delay(1000);
        gas_O3.setTempCompensation(gas_O3.ON);
    }
    
}

// Helper Gas Functions
float readNO2(void){
    return gas_NO2.readGasConcentrationPPM();
}

float readO3(void){
    return gas_O3.readGasConcentrationPPM();
}

bool NO2Connected(void) {
    // dataIsAvailable() sends an I2C request, verifies the 9-byte packet, 
    // and returns false if the sensor fails to respond or fails the checksum.
    return gas_NO2.dataIsAvailable();
}
bool O3Connected(void) {
    return gas_O3.dataIsAvailable();
}