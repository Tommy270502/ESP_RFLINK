#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include "Config.h"

class RadioService {
public:
  bool begin();
  bool applyConfig();
  bool send(const uint8_t* data, size_t len, bool requireAck = false);
  bool startListening();
  bool stopListening();
  bool flushRx();
  bool flushTx();
  bool setRxAddress(const uint8_t* address, size_t len);
  bool setTxAddress(const uint8_t* address, size_t len);
  bool isChipConnected();
  void fillConfig(JsonObject data);
  void poll();
  void setPacketCallback(void (*callback)(const uint8_t* data, size_t len));

private:
  bool setAddress(uint8_t* target, const uint8_t* address, size_t len);
  void (*onPacket)(const uint8_t* data, size_t len) = nullptr;
};

extern RadioService radioService;
