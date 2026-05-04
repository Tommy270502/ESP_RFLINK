#pragma once
#include <Arduino.h>

class WebService {
public:
  void begin();
  void poll();
  void broadcastRfPacket(const uint8_t* data, size_t len);
  void broadcastStatus();

private:
  void setupRoutes();
};

extern WebService webService;
