#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

enum class CommandTransport {
  Serial,
  Http,
  WebSocket,
  Ble,
};

class CommandService {
public:
  void pollSerial();
  void handle(JsonDocument& req, JsonDocument& res, CommandTransport transport = CommandTransport::Serial);
  JsonObject makeOk(JsonDocument& res, const char* cmd);
  void makeError(JsonDocument& res, const char* cmd, const char* code, const char* message);
};

extern CommandService commandService;
