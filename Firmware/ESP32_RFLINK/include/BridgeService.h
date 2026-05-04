#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

class BridgeService {
public:
  void begin();
  void handleRfPacket(const uint8_t* data, size_t len);
  void setRfToWifiEnabled(bool enabled);
  void setRfToBleEnabled(bool enabled);
  bool rfToWifiEnabled() const;
  bool rfToBleEnabled() const;
  void fillStatus(JsonObject data) const;
};

extern BridgeService bridgeService;
