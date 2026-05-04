#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

class BleService {
public:
  void begin();
  void poll();
  bool enabled() const;
  bool connected() const;
  void fillStatus(JsonObject data) const;
  void notifyJson(const JsonDocument& doc);
  void notifyRfPacket(const uint8_t* data, size_t len);
  void appendRx(const uint8_t* data, size_t len);
  void setConnected(bool isConnected);

private:
  void processRxBuffer();
  void handleLine(const String& line);
  void notifyLine(const String& line);

  bool bleEnabled = false;
  bool bleConnected = false;
  bool rxOverflow = false;
  String rxBuffer;
};

extern BleService bleService;
