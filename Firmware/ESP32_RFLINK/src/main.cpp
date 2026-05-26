#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "Config.h"
#include "Utils.h"
#include "RadioService.h"
#include "SettingsService.h"
#include "BridgeService.h"
#include "BleService.h"
#include "CommandService.h"
#include "WebService.h"
#include "AppState.h"

static void onRfPacket(const uint8_t* data, size_t len) {
  bridgeService.handleRfPacket(data, len);
}

static void emitBootMessage(bool rfOk) {
  JsonDocument doc;
  doc["type"] = "boot";
  doc["ok"] = true;
  doc["cmd"] = "boot";
  JsonObject data = doc["data"].to<JsonObject>();
  data["product"] = "WirelessDevBridge";
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["uptime_ms"] = millis();
  data["radio_initialized"] = rfOk;
  data["radio_chip_connected"] = radioService.isChipConnected();
  data["ap_ssid"] = settingsService.apSsid();
  data["ap_ip"] = WiFi.softAPIP().toString();
  data["ble_enabled"] = bleService.enabled();
  data["ble_name"] = settingsService.bleName();
  data["settings_loaded"] = settingsService.loadedFromNvs();
  doc["error"] = nullptr;
  sendJsonSerial(doc);
}

void setup() {
  pinMode(Config::PIN_LED, OUTPUT);
  digitalWrite(Config::PIN_LED, LOW);

  Serial.begin(115200);
  delay(500);

  settingsService.begin();
  bool rfOk = radioService.begin();
  radioService.setPacketCallback(onRfPacket);

  bridgeService.begin();
  webService.begin();
  bleService.begin();
  emitBootMessage(rfOk);
  eventLog.add("boot", rfOk ? "ok" : "radio init failed");

  digitalWrite(Config::PIN_LED, HIGH);
}

void loop() {
  commandService.pollSerial();
  radioService.poll();
  webService.poll();
  bleService.poll();

  static uint32_t lastStatus = 0;
  if (millis() - lastStatus > 5000) {
    lastStatus = millis();
    webService.broadcastStatus();
  }
}
