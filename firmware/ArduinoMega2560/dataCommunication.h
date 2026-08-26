#ifndef DATA_COMM_H
#define DATA_COMM_H
#include "config.h"

void initCommunication();
void processPiCommands();
bool isPiConnected();
void sendDataToPi(JsonDocument& doc);
void saveDataToSD(JsonDocument& doc);

#endif