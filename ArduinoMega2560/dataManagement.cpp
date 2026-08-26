#include "dataManagement.h"
#include "dataCommunication.h"
#include "sensors.h"

void updateSystemData(SystemData& data){
    // Grab GPS data(returns false if disconnected, but leaves old data or 0s)
    logLocationData(data.gps);
    logTimeData(data.gps);

    // Grab Gas data (using -1.0 as an error/disconnected flag)
    if(NO2Connected()){
        data.no2_ppm = readNO2();
    } else{
        data.no2_ppm = -1.0;
    }

    if(O3Connected()){
        data.o3_ppm = readO3();
    } else{
        data.o3_ppm = -1.0;
    }
}

void processAndRouteData(SystemData& data){
// 1. Refresh the data struct
    updateSystemData(data);
    
//2. Build JSON Document
    JsonDocument doc;
    doc["lat"] = data.latitude;
    doc["long"] = data.longitude;
    doc["alt"] = data.gps.altitude;
    doc["siv"] = data.gps.SIV;
    
    // Format time into standard ISO 8601 string (YYY-MM-DDTHH:MM:SS)
    char timeString[25];
    snprintf(timeString, sizeof(timeString), "%04d-%02d-%02dT%02d:%02d:%02d",
             data.gps.year, data.gps.month, data.gps.day,
             data.gps.hour, data.gps.minute, data.gps.second
    );
    doc["time"] = timeString;
    doc["no2"] = data.no2_ppm;
    doc["o3"] = data.o3_ppm;    

// 3. Send to Communication Layer
    if(isPiConnected()){
        sendDataToPi(doc);
    } else{
        saveDataToSD(doc);
    }
}