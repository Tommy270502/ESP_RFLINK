#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

class CommandService {
public:
  void pollSerial();
  void handle(JsonDocument& req, JsonDocument& res);
  JsonObject makeOk(JsonDocument& res, const char* cmd);
  void makeError(JsonDocument& res, const char* cmd, const char* code, const char* message);
};

extern CommandService commandService;
