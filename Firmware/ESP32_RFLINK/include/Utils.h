#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <RF24.h>

String bytesToHex(const uint8_t* data, size_t len);
bool hexToBytes(const String& hex, uint8_t* out, size_t& outLen, size_t maxLen);
bool parseRadioAddress(const String& value, const String& format, uint8_t* out, size_t len);
String bytesToPrintableAscii(const uint8_t* data, size_t len);
String datarateToString(rf24_datarate_e r);
String powerToString(rf24_pa_dbm_e p);
bool parseDatarate(const String& s, rf24_datarate_e& out);
bool parsePower(const String& s, rf24_pa_dbm_e& out);
void sendJsonSerial(const JsonDocument& doc);
