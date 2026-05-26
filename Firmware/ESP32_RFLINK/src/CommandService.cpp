#include "CommandService.h"
#include "Config.h"
#include "AppState.h"
#include "Utils.h"
#include "RadioService.h"
#include "BridgeService.h"
#include "BleService.h"
#include "SettingsService.h"
#include <WiFi.h>
#include <esp_system.h>
#include <string.h>

CommandService commandService;

static void fillStats(JsonObject data) {
  data["rf_rx"] = stats.rfRx;
  data["rf_tx"] = stats.rfTx;
  data["rf_tx_attempts"] = stats.rfTxAttempts;
  data["rf_tx_fail"] = stats.rfTxFail;
  data["rf_rx_invalid"] = stats.rfRxInvalid;
  data["ws_rx"] = stats.wsRx;
  data["ble_rx"] = stats.bleRx;
  data["serial_rx"] = stats.serialRx;
  data["last_packet_ms"] = stats.lastPacketMs;
  data["last_packet_len"] = stats.lastPacketLen;
  if (stats.rfTxAttempts > 0) {
    data["ack_failure_rate"] = static_cast<float>(stats.rfTxFail) / static_cast<float>(stats.rfTxAttempts);
  } else {
    data["ack_failure_rate"] = 0;
  }
}

static void fillWifiStatus(JsonObject data) {
  const bool apMode = WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA;
  data["ap_mode"] = apMode;
  data["ssid"] = settingsService.apSsid();
  data["ip"] = WiFi.softAPIP().toString();
  data["clients"] = WiFi.softAPgetStationNum();
}

static String deviceId() {
  uint64_t mac = ESP.getEfuseMac();
  char id[17];
  snprintf(id, sizeof(id), "%04X%08X", static_cast<uint16_t>(mac >> 32), static_cast<uint32_t>(mac));
  return String(id);
}

static const char* resetReasonToString(esp_reset_reason_t reason) {
  switch (reason) {
    case ESP_RST_POWERON: return "power_on";
    case ESP_RST_EXT: return "external";
    case ESP_RST_SW: return "software";
    case ESP_RST_PANIC: return "panic";
    case ESP_RST_INT_WDT: return "interrupt_watchdog";
    case ESP_RST_TASK_WDT: return "task_watchdog";
    case ESP_RST_WDT: return "watchdog";
    case ESP_RST_DEEPSLEEP: return "deep_sleep";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_SDIO: return "sdio";
    default: return "unknown";
  }
}

static void fillLastError(JsonObject data) {
  if (lastErrorCode.length() == 0) {
    data["last_error"] = nullptr;
    return;
  }

  JsonObject error = data["last_error"].to<JsonObject>();
  error["code"] = lastErrorCode;
  error["message"] = lastErrorMessage;
}

static void fillStatus(JsonObject data) {
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["uptime_ms"] = millis();

  JsonObject radio = data["radio"].to<JsonObject>();
  radioService.fillConfig(radio);

  JsonObject wifi = data["wifi"].to<JsonObject>();
  fillWifiStatus(wifi);

  JsonObject bridge = data["bridge"].to<JsonObject>();
  bridgeService.fillStatus(bridge);

  JsonObject ble = data["ble"].to<JsonObject>();
  bleService.fillStatus(ble);

  JsonObject statData = data["stats"].to<JsonObject>();
  fillStats(statData);

  JsonObject device = data["device"].to<JsonObject>();
  settingsService.fillDevice(device);
  device["id"] = deviceId();
  device["fw"] = Config::FW_VERSION;
  device["protocol"] = Config::PROTOCOL_VERSION;
  device["softap_mac"] = WiFi.softAPmacAddress();

  JsonObject storage = data["storage"].to<JsonObject>();
  settingsService.fillStorage(storage);

  JsonObject security = data["security"].to<JsonObject>();
  settingsService.fillSecurity(security);

  data["reset_reason"] = resetReasonToString(esp_reset_reason());
  fillLastError(data);
}

static void fillCapabilities(JsonObject data) {
  data["product"] = "WirelessDevBridge";
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["settings_persistence"] = true;
  data["settings_schema_version"] = SETTINGS_SCHEMA_VERSION;
  data["optional_auth"] = true;

  JsonObject build = data["build"].to<JsonObject>();
  build["profile"] = BUILD_PROFILE;
  build["date"] = BUILD_DATE;
  if (strlen(GIT_SHA) > 0) build["git_sha"] = GIT_SHA;

  JsonObject transports = data["transports"].to<JsonObject>();
  transports["usb_serial_jsonl"] = true;
  transports["http_json"] = true;
  transports["websocket_json"] = true;
  transports["ble_gatt"] = Config::BLE_ENABLE;

  JsonObject ble = data["ble"].to<JsonObject>();
  ble["service_uuid"] = Config::BLE_SERVICE_UUID;
  ble["rx_uuid"] = Config::BLE_RX_UUID;
  ble["tx_uuid"] = Config::BLE_TX_UUID;
  ble["framing"] = "newline_json";
  ble["notify_chunk_size"] = Config::BLE_NOTIFY_CHUNK_SIZE;

  JsonObject radio = data["radio"].to<JsonObject>();
  radio["nrf24"] = true;
  radio["payload_max"] = Config::RF_PAYLOAD_MAX;
  radio["address_width"] = Config::RF_ADDRESS_WIDTH;
  radio["channel_min"] = 0;
  radio["channel_max"] = 125;

  JsonArray commands = data["commands"].to<JsonArray>();
  commands.add("ping");
  commands.add("protocol");
  commands.add("capabilities");
  commands.add("status");
  commands.add("self_test");
  commands.add("rf_config");
  commands.add("rf_get_config");
  commands.add("rf_send");
  commands.add("rf_start_listen");
  commands.add("rf_stop_listen");
  commands.add("rf_flush_rx");
  commands.add("rf_flush_tx");
  commands.add("rf_set_address");
  commands.add("bridge");
  commands.add("settings_get");
  commands.add("settings_set");
  commands.add("settings_save");
  commands.add("settings_reset");
  commands.add("diagnostics");
  commands.add("identify");
  commands.add("rf_metrics");
  commands.add("rf_profiles");
  commands.add("rf_apply_profile");
  commands.add("event_log");
}

static bool readStringArg(JsonDocument& req, const char* key, String& out) {
  JsonVariant arg = req[key];
  if (arg.isNull() || !arg.is<const char*>()) return false;

  out = arg.as<const char*>();
  out.trim();
  return true;
}

static bool isHexPayloadTooLong(const String& hex) {
  String s = hex;
  s.trim();
  if (s.startsWith("0x") || s.startsWith("0X")) s = s.substring(2);
  return (s.length() / 2) > Config::RF_PAYLOAD_MAX;
}

JsonObject CommandService::makeOk(JsonDocument& res, const char* cmd) {
  res.clear();
  res["ok"] = true;
  res["cmd"] = cmd;
  JsonObject data = res["data"].to<JsonObject>();
  res["error"] = nullptr;
  return data;
}

void CommandService::makeError(JsonDocument& res, const char* cmd, const char* code, const char* message) {
  res.clear();
  res["ok"] = false;
  res["cmd"] = cmd;
  res["data"].to<JsonObject>();
  JsonObject error = res["error"].to<JsonObject>();
  error["code"] = code;
  error["message"] = message;
  lastErrorCode = code;
  lastErrorMessage = message;
  eventLog.add("cmd_error", code);
}

static void handleRfConfig(JsonDocument& req, JsonDocument& res) {
  uint8_t newChannel = rfCfg.channel;
  rf24_datarate_e newDatarate = rfCfg.datarate;
  rf24_pa_dbm_e newPower = rfCfg.power;
  bool newAutoAck = rfCfg.autoAck;

  JsonVariant channelArg = req["channel"];
  if (!channelArg.isNull()) {
    if (!channelArg.is<int>()) {
      commandService.makeError(res, "rf_config", "invalid_arg", "channel must be a number");
      return;
    }
    int ch = channelArg.as<int>();
    if (ch < 0 || ch > 125) {
      commandService.makeError(res, "rf_config", "invalid_channel", "channel must be 0..125");
      return;
    }
    newChannel = static_cast<uint8_t>(ch);
  }

  String datarateString;
  if (!req["datarate"].isNull()) {
    if (!readStringArg(req, "datarate", datarateString)) {
      commandService.makeError(res, "rf_config", "invalid_arg", "datarate must be a string");
      return;
    }
    if (!parseDatarate(datarateString, newDatarate)) {
      commandService.makeError(res, "rf_config", "invalid_datarate", "datarate must be 250kbps, 1mbps, or 2mbps");
      return;
    }
  }

  String powerString;
  if (!req["power"].isNull()) {
    if (!readStringArg(req, "power", powerString)) {
      commandService.makeError(res, "rf_config", "invalid_arg", "power must be a string");
      return;
    }
    if (!parsePower(powerString, newPower)) {
      commandService.makeError(res, "rf_config", "invalid_power", "power must be min, low, high, or max");
      return;
    }
  }

  JsonVariant autoAckArg = req["auto_ack"];
  if (!autoAckArg.isNull()) {
    if (!autoAckArg.is<bool>()) {
      commandService.makeError(res, "rf_config", "invalid_arg", "auto_ack must be true or false");
      return;
    }
    newAutoAck = autoAckArg.as<bool>();
  }

  rfCfg.channel = newChannel;
  rfCfg.datarate = newDatarate;
  rfCfg.power = newPower;
  rfCfg.autoAck = newAutoAck;

  if (!radioService.applyConfig()) {
    commandService.makeError(res, "rf_config", "radio_not_initialized", "radio not initialized");
    return;
  }

  settingsService.markDirty();
  JsonObject data = commandService.makeOk(res, "rf_config");
  radioService.fillConfig(data);
}

static void handleRfSend(JsonDocument& req, JsonDocument& res) {
  String hex;
  if (!readStringArg(req, "hex", hex)) {
    commandService.makeError(res, "rf_send", "missing_arg", "hex payload is required");
    return;
  }

  String normalized = hex;
  normalized.trim();
  if (normalized.startsWith("0x") || normalized.startsWith("0X")) normalized = normalized.substring(2);
  if (normalized.length() == 0) {
    commandService.makeError(res, "rf_send", "empty_payload", "payload must not be empty");
    return;
  }
  if (normalized.length() % 2 != 0) {
    commandService.makeError(res, "rf_send", "invalid_hex", "hex payload must contain an even number of characters");
    return;
  }
  if (isHexPayloadTooLong(hex)) {
    commandService.makeError(res, "rf_send", "payload_too_large", "payload must be 32 bytes or less");
    return;
  }
  if (!rfCfg.initialized) {
    commandService.makeError(res, "rf_send", "radio_not_initialized", "radio not initialized");
    return;
  }

  JsonVariant requireAckArg = req["require_ack"];
  bool requireAck = false;
  if (!requireAckArg.isNull()) {
    if (!requireAckArg.is<bool>()) {
      commandService.makeError(res, "rf_send", "invalid_arg", "require_ack must be true or false");
      return;
    }
    requireAck = requireAckArg.as<bool>();
  }

  uint8_t dataBytes[Config::RF_PAYLOAD_MAX];
  size_t len = 0;
  if (!hexToBytes(hex, dataBytes, len, sizeof(dataBytes))) {
    commandService.makeError(res, "rf_send", "invalid_hex", "hex payload contains non-hex characters");
    return;
  }

  bool sent = radioService.send(dataBytes, len, requireAck);
  if (!sent) {
    commandService.makeError(
      res,
      "rf_send",
      requireAck ? "ack_timeout" : "rf_send_failed",
      requireAck ? "radio write failed; no ACK received" : "radio write failed"
    );
    return;
  }

  JsonObject data = commandService.makeOk(res, "rf_send");
  data["sent"] = true;
  data["require_ack"] = requireAck;
  data["len"] = len;
  data["hex"] = bytesToHex(dataBytes, len);
}

static void handleRfSetAddress(JsonDocument& req, JsonDocument& res) {
  String format = req["format"] | "";
  bool changed = false;
  uint8_t address[Config::RF_ADDRESS_WIDTH];

  String rx;
  if (!req["rx"].isNull()) {
    if (!readStringArg(req, "rx", rx) || !parseRadioAddress(rx, format, address, sizeof(address))) {
      commandService.makeError(res, "rf_set_address", "invalid_address", "rx address must be 5 ASCII chars or 5 bytes as hex");
      return;
    }
    if (!radioService.setRxAddress(address, sizeof(address))) {
      commandService.makeError(res, "rf_set_address", "radio_not_initialized", "radio not initialized");
      return;
    }
    changed = true;
  }

  String tx;
  if (!req["tx"].isNull()) {
    if (!readStringArg(req, "tx", tx) || !parseRadioAddress(tx, format, address, sizeof(address))) {
      commandService.makeError(res, "rf_set_address", "invalid_address", "tx address must be 5 ASCII chars or 5 bytes as hex");
      return;
    }
    if (!radioService.setTxAddress(address, sizeof(address))) {
      commandService.makeError(res, "rf_set_address", "radio_not_initialized", "radio not initialized");
      return;
    }
    changed = true;
  }

  if (!changed) {
    String pipe;
    String value;
    if (!readStringArg(req, "pipe", pipe) || !readStringArg(req, "address", value)) {
      commandService.makeError(res, "rf_set_address", "missing_arg", "provide rx/tx fields or pipe plus address");
      return;
    }

    if (!parseRadioAddress(value, format, address, sizeof(address))) {
      commandService.makeError(res, "rf_set_address", "invalid_address", "address must be 5 ASCII chars or 5 bytes as hex");
      return;
    }

    pipe.toLowerCase();
    if (pipe == "rx") {
      changed = radioService.setRxAddress(address, sizeof(address));
    } else if (pipe == "tx") {
      changed = radioService.setTxAddress(address, sizeof(address));
    } else {
      commandService.makeError(res, "rf_set_address", "invalid_pipe", "pipe must be rx or tx");
      return;
    }

    if (!changed) {
      commandService.makeError(res, "rf_set_address", "radio_not_initialized", "radio not initialized");
      return;
    }
  }

  settingsService.markDirty();
  JsonObject data = commandService.makeOk(res, "rf_set_address");
  radioService.fillConfig(data);
}

static void handleBridge(JsonDocument& req, JsonDocument& res) {
  JsonVariant rfToWifi = req["rf_to_wifi"];
  if (!rfToWifi.isNull()) {
    if (!rfToWifi.is<bool>()) {
      commandService.makeError(res, "bridge", "invalid_arg", "rf_to_wifi must be true or false");
      return;
    }
    bridgeService.setRfToWifiEnabled(rfToWifi.as<bool>());
  }

  JsonVariant rfToBle = req["rf_to_ble"];
  if (!rfToBle.isNull()) {
    if (!rfToBle.is<bool>()) {
      commandService.makeError(res, "bridge", "invalid_arg", "rf_to_ble must be true or false");
      return;
    }
    bridgeService.setRfToBleEnabled(rfToBle.as<bool>());
  }

  settingsService.markDirty();
  JsonObject data = commandService.makeOk(res, "bridge");
  bridgeService.fillStatus(data);
}

static bool readStringMember(JsonObject obj, const char* key, String& out) {
  JsonVariant arg = obj[key];
  if (arg.isNull() || !arg.is<const char*>()) return false;

  out = arg.as<const char*>();
  out.trim();
  return true;
}

static void fillSelfTest(JsonObject data) {
  data["product"] = "WirelessDevBridge";
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["uptime_ms"] = millis();
  data["radio_initialized"] = rfCfg.initialized;
  data["radio_chip_connected"] = radioService.isChipConnected();
  data["wifi_ap_mode"] = WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA;
  data["wifi_ap_ip"] = WiFi.softAPIP().toString();
  data["wifi_clients"] = WiFi.softAPgetStationNum();
  data["ble_enabled"] = bleService.enabled();
  data["ble_connected"] = bleService.connected();
  data["ble_name"] = settingsService.bleName();
  data["free_heap"] = ESP.getFreeHeap();
  data["heap_size"] = ESP.getHeapSize();
  data["settings_loaded"] = settingsService.loadedFromNvs();
}

static void handleSettingsGet(JsonDocument& res) {
  JsonObject data = commandService.makeOk(res, "settings_get");
  settingsService.fillSettings(data);
}

static bool applySettingsAddress(JsonObject rf, const char* key, bool rxPipe, const String& format, JsonDocument& res) {
  if (rf[key].isNull()) return true;

  String value;
  uint8_t address[Config::RF_ADDRESS_WIDTH];
  if (!readStringMember(rf, key, value) || !parseRadioAddress(value, format, address, sizeof(address))) {
    commandService.makeError(res, "settings_set", "invalid_address", "address must be 5 ASCII chars or 5 bytes as hex");
    return false;
  }

  bool ok = rxPipe ? radioService.setRxAddress(address, sizeof(address)) : radioService.setTxAddress(address, sizeof(address));
  if (!ok) {
    commandService.makeError(res, "settings_set", "radio_not_initialized", "radio not initialized");
    return false;
  }
  return true;
}

static bool applySettingsObject(JsonDocument& req, JsonDocument& res) {
  if (!req["rf"].isNull()) {
    if (!req["rf"].is<JsonObject>()) {
      commandService.makeError(res, "settings_set", "invalid_arg", "rf must be an object");
      return false;
    }
    JsonObject rf = req["rf"].as<JsonObject>();

    JsonDocument rfReq;
    rfReq["cmd"] = "rf_config";
    if (!rf["channel"].isNull()) rfReq["channel"] = rf["channel"];
    if (!rf["datarate"].isNull()) rfReq["datarate"] = rf["datarate"];
    if (!rf["power"].isNull()) rfReq["power"] = rf["power"];
    if (!rf["auto_ack"].isNull()) rfReq["auto_ack"] = rf["auto_ack"];
    handleRfConfig(rfReq, res);
    if (!res["ok"].as<bool>()) return false;

    String format = rf["address_format"] | "ascii";
    if (!applySettingsAddress(rf, "rx", true, format, res)) return false;
    if (!applySettingsAddress(rf, "tx", false, format, res)) return false;
  }

  if (!req["bridge"].isNull()) {
    if (!req["bridge"].is<JsonObject>()) {
      commandService.makeError(res, "settings_set", "invalid_arg", "bridge must be an object");
      return false;
    }
    JsonObject bridge = req["bridge"].as<JsonObject>();
    JsonVariant rfToWifi = bridge["rf_to_wifi"];
    if (!rfToWifi.isNull()) {
      if (!rfToWifi.is<bool>()) {
        commandService.makeError(res, "settings_set", "invalid_arg", "bridge.rf_to_wifi must be true or false");
        return false;
      }
      bridgeService.setRfToWifiEnabled(rfToWifi.as<bool>());
    }
    JsonVariant rfToBle = bridge["rf_to_ble"];
    if (!rfToBle.isNull()) {
      if (!rfToBle.is<bool>()) {
        commandService.makeError(res, "settings_set", "invalid_arg", "bridge.rf_to_ble must be true or false");
        return false;
      }
      bridgeService.setRfToBleEnabled(rfToBle.as<bool>());
    }
  }

  if (!req["device"].isNull()) {
    if (!req["device"].is<JsonObject>()) {
      commandService.makeError(res, "settings_set", "invalid_arg", "device must be an object");
      return false;
    }
    JsonObject device = req["device"].as<JsonObject>();
    String value;
    if (!device["name"].isNull()) {
      if (!readStringMember(device, "name", value) || !settingsService.setDeviceName(value)) {
        commandService.makeError(res, "settings_set", "invalid_setting", "device.name must be 1..32 characters");
        return false;
      }
    }
    if (!device["ap_ssid"].isNull()) {
      if (!readStringMember(device, "ap_ssid", value) || !settingsService.setApSsid(value)) {
        commandService.makeError(res, "settings_set", "invalid_setting", "device.ap_ssid must be 1..32 characters");
        return false;
      }
    }
    if (!device["ap_pass"].isNull()) {
      if (!readStringMember(device, "ap_pass", value) || !settingsService.setApPass(value)) {
        commandService.makeError(res, "settings_set", "invalid_setting", "device.ap_pass must be 8..63 characters");
        return false;
      }
    }
    if (!device["ble_name"].isNull()) {
      if (!readStringMember(device, "ble_name", value) || !settingsService.setBleName(value)) {
        commandService.makeError(res, "settings_set", "invalid_setting", "device.ble_name must be 1..32 characters");
        return false;
      }
    }
  }

  if (!req["security"].isNull()) {
    if (!req["security"].is<JsonObject>()) {
      commandService.makeError(res, "settings_set", "invalid_arg", "security must be an object");
      return false;
    }
    JsonObject security = req["security"].as<JsonObject>();
    JsonVariant authRequired = security["auth_required"];
    if (!authRequired.isNull()) {
      if (!authRequired.is<bool>()) {
        commandService.makeError(res, "settings_set", "invalid_arg", "security.auth_required must be true or false");
        return false;
      }
      settingsService.setAuthRequired(authRequired.as<bool>());
    }
    if (!security["auth_token"].isNull()) {
      String token;
      if (!readStringMember(security, "auth_token", token) || !settingsService.setAuthToken(token)) {
        commandService.makeError(res, "settings_set", "invalid_setting", "security.auth_token must be 64 characters or fewer");
        return false;
      }
    }
  }

  settingsService.markDirty();
  return true;
}

static void handleSettingsSet(JsonDocument& req, JsonDocument& res) {
  if (!applySettingsObject(req, res)) return;

  JsonObject data = commandService.makeOk(res, "settings_set");
  settingsService.fillSettings(data);
}

static void handleSettingsSave(JsonDocument& res) {
  if (!settingsService.save()) {
    commandService.makeError(res, "settings_save", "nvs_error", "failed to save settings");
    eventLog.add("settings", "save failed");
    return;
  }

  eventLog.add("settings", "saved");
  JsonObject data = commandService.makeOk(res, "settings_save");
  settingsService.fillSettings(data);
}

static void handleSettingsReset(JsonDocument& res) {
  if (!settingsService.reset()) {
    commandService.makeError(res, "settings_reset", "nvs_error", "failed to reset settings");
    eventLog.add("settings", "reset failed");
    return;
  }

  eventLog.add("settings", "reset to defaults");
  JsonObject data = commandService.makeOk(res, "settings_reset");
  settingsService.fillSettings(data);
}

static void fillDiagnostics(JsonObject data) {
  JsonObject selfTest = data["self_test"].to<JsonObject>();
  fillSelfTest(selfTest);

  data["reset_reason"] = resetReasonToString(esp_reset_reason());
  data["uptime_ms"] = millis();
  data["free_heap"] = ESP.getFreeHeap();
  data["heap_size"] = ESP.getHeapSize();
  data["sdk_version"] = ESP.getSdkVersion();

  JsonObject build = data["build"].to<JsonObject>();
  build["profile"] = BUILD_PROFILE;
  build["date"] = BUILD_DATE;
  if (strlen(GIT_SHA) > 0) build["git_sha"] = GIT_SHA;

  JsonObject chip = data["chip"].to<JsonObject>();
  chip["model"] = ESP.getChipModel();
  chip["revision"] = ESP.getChipRevision();
  chip["cores"] = ESP.getChipCores();
  chip["flash_size"] = ESP.getFlashChipSize();
  chip["efuse_mac"] = deviceId();

  JsonObject status = data["status"].to<JsonObject>();
  fillStatus(status);

  JsonObject settings = data["settings"].to<JsonObject>();
  settingsService.fillSettings(settings);

  data["event_log_count"] = eventLog.count();
}

struct RfProfile {
  const char* name;
  uint8_t channel;
  rf24_datarate_e datarate;
  rf24_pa_dbm_e power;
  bool autoAck;
};

static const RfProfile rfProfiles[] = {
  {"lab",             76, RF24_1MBPS,   RF24_PA_LOW,  true},
  {"low_power",       76, RF24_250KBPS, RF24_PA_MIN,  true},
  {"range_test",       2, RF24_250KBPS, RF24_PA_MAX,  true},
  {"production_test", 76, RF24_1MBPS,   RF24_PA_HIGH, true},
};
static constexpr size_t RF_PROFILE_COUNT = sizeof(rfProfiles) / sizeof(rfProfiles[0]);

static void handleDiagnostics(JsonDocument& res) {
  JsonObject data = commandService.makeOk(res, "diagnostics");
  fillDiagnostics(data);
}

static void fillIdentity(JsonObject data) {
  data["product"] = "WirelessDevBridge";
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["id"] = deviceId();
  data["ap_ssid"] = settingsService.apSsid();
  data["ap_ip"] = WiFi.softAPIP().toString();
  data["softap_mac"] = WiFi.softAPmacAddress();
  data["ble_name"] = settingsService.bleName();
}

static void handleIdentify(JsonDocument& res) {
  bool previous = digitalRead(Config::PIN_LED);
  for (uint8_t i = 0; i < 3; i++) {
    digitalWrite(Config::PIN_LED, LOW);
    delay(90);
    digitalWrite(Config::PIN_LED, HIGH);
    delay(90);
  }
  digitalWrite(Config::PIN_LED, previous);

  JsonObject data = commandService.makeOk(res, "identify");
  fillIdentity(data);
}

static bool authExempt(const char* cmd) {
  return strcmp(cmd, "ping") == 0 || strcmp(cmd, "protocol") == 0 || strcmp(cmd, "capabilities") == 0;
}

void CommandService::handle(JsonDocument& req, JsonDocument& res, CommandTransport transport) {
  const char* cmd = req["cmd"] | "";

  if (strlen(cmd) == 0) {
    makeError(res, "", "missing_cmd", "cmd is required");
    return;
  }

  if (transport != CommandTransport::Serial && settingsService.authRequired() && !authExempt(cmd)) {
    const char* token = req["auth"] | "";
    if (!settingsService.checkAuth(token)) {
      makeError(res, cmd, "auth_required", "valid auth token required");
      return;
    }
  }

  if (strcmp(cmd, "ping") == 0) {
    JsonObject data = makeOk(res, cmd);
    data["pong"] = true;
    data["fw"] = Config::FW_VERSION;
    data["protocol"] = Config::PROTOCOL_VERSION;
    data["uptime_ms"] = millis();
  }
  else if (strcmp(cmd, "protocol") == 0 || strcmp(cmd, "capabilities") == 0) {
    JsonObject data = makeOk(res, cmd);
    fillCapabilities(data);
  }
  else if (strcmp(cmd, "status") == 0) {
    JsonObject data = makeOk(res, cmd);
    fillStatus(data);
  }
  else if (strcmp(cmd, "self_test") == 0) {
    JsonObject data = makeOk(res, cmd);
    fillSelfTest(data);
  }
  else if (strcmp(cmd, "rf_config") == 0) {
    handleRfConfig(req, res);
  }
  else if (strcmp(cmd, "rf_get_config") == 0) {
    JsonObject data = makeOk(res, cmd);
    radioService.fillConfig(data);
  }
  else if (strcmp(cmd, "rf_start_listen") == 0) {
    if (!radioService.startListening()) {
      makeError(res, cmd, "radio_not_initialized", "radio not initialized");
      return;
    }
    JsonObject data = makeOk(res, cmd);
    data["listening"] = rfCfg.listening;
  }
  else if (strcmp(cmd, "rf_stop_listen") == 0) {
    if (!radioService.stopListening()) {
      makeError(res, cmd, "radio_not_initialized", "radio not initialized");
      return;
    }
    JsonObject data = makeOk(res, cmd);
    data["listening"] = rfCfg.listening;
  }
  else if (strcmp(cmd, "rf_listen") == 0) {
    JsonVariant enableArg = req["enable"];
    bool enable = true;
    if (!enableArg.isNull()) {
      if (!enableArg.is<bool>()) {
        makeError(res, cmd, "invalid_arg", "enable must be true or false");
        return;
      }
      enable = enableArg.as<bool>();
    }
    req["cmd"] = enable ? "rf_start_listen" : "rf_stop_listen";
    handle(req, res);
    res["cmd"] = "rf_listen";
  }
  else if (strcmp(cmd, "rf_flush_rx") == 0) {
    if (!radioService.flushRx()) {
      makeError(res, cmd, "radio_not_initialized", "radio not initialized");
      return;
    }
    JsonObject data = makeOk(res, cmd);
    data["flushed"] = "rx";
  }
  else if (strcmp(cmd, "rf_flush_tx") == 0) {
    if (!radioService.flushTx()) {
      makeError(res, cmd, "radio_not_initialized", "radio not initialized");
      return;
    }
    JsonObject data = makeOk(res, cmd);
    data["flushed"] = "tx";
  }
  else if (strcmp(cmd, "rf_set_address") == 0) {
    handleRfSetAddress(req, res);
  }
  else if (strcmp(cmd, "rf_send") == 0) {
    handleRfSend(req, res);
  }
  else if (strcmp(cmd, "bridge") == 0) {
    handleBridge(req, res);
  }
  else if (strcmp(cmd, "settings_get") == 0) {
    handleSettingsGet(res);
  }
  else if (strcmp(cmd, "settings_set") == 0) {
    handleSettingsSet(req, res);
  }
  else if (strcmp(cmd, "settings_save") == 0) {
    handleSettingsSave(res);
  }
  else if (strcmp(cmd, "settings_reset") == 0) {
    handleSettingsReset(res);
  }
  else if (strcmp(cmd, "diagnostics") == 0) {
    handleDiagnostics(res);
  }
  else if (strcmp(cmd, "identify") == 0) {
    handleIdentify(res);
  }
  else if (strcmp(cmd, "rf_metrics") == 0) {
    JsonObject data = makeOk(res, cmd);
    fillStats(data);
  }
  else if (strcmp(cmd, "rf_profiles") == 0) {
    JsonObject data = makeOk(res, cmd);
    JsonArray profiles = data["profiles"].to<JsonArray>();
    for (size_t i = 0; i < RF_PROFILE_COUNT; i++) {
      JsonObject p = profiles.add<JsonObject>();
      p["name"] = rfProfiles[i].name;
      p["channel"] = rfProfiles[i].channel;
      p["datarate"] = datarateToString(rfProfiles[i].datarate);
      p["power"] = powerToString(rfProfiles[i].power);
      p["auto_ack"] = rfProfiles[i].autoAck;
    }
  }
  else if (strcmp(cmd, "rf_apply_profile") == 0) {
    String profileName;
    if (!readStringArg(req, "name", profileName)) {
      makeError(res, cmd, "missing_arg", "name is required");
      return;
    }
    const RfProfile* match = nullptr;
    for (size_t i = 0; i < RF_PROFILE_COUNT; i++) {
      if (profileName.equalsIgnoreCase(rfProfiles[i].name)) {
        match = &rfProfiles[i];
        break;
      }
    }
    if (!match) {
      makeError(res, cmd, "invalid_arg", "unknown RF profile name");
      return;
    }
    rfCfg.channel = match->channel;
    rfCfg.datarate = match->datarate;
    rfCfg.power = match->power;
    rfCfg.autoAck = match->autoAck;
    if (!radioService.applyConfig()) {
      makeError(res, cmd, "radio_not_initialized", "radio not initialized");
      return;
    }
    settingsService.markDirty();
    JsonObject data = makeOk(res, cmd);
    data["profile"] = match->name;
    radioService.fillConfig(data);
  }
  else if (strcmp(cmd, "event_log") == 0) {
    JsonObject data = makeOk(res, cmd);
    data["count"] = eventLog.count();
    JsonArray entries = data["entries"].to<JsonArray>();
    for (size_t i = 0; i < eventLog.count(); i++) {
      const EventLogEntry& entry = eventLog.at(i);
      JsonObject e = entries.add<JsonObject>();
      e["ms"] = entry.timestampMs;
      e["type"] = entry.type;
      e["detail"] = entry.detail;
    }
  }
  else {
    makeError(res, cmd, "unknown_cmd", "unknown command");
  }
}

void CommandService::pollSerial() {
  static String line;
  static bool lineOverflow = false;

  while (Serial.available()) {
    char c = static_cast<char>(Serial.read());

    if (c == '\n' || c == '\r') {
      line.trim();
      if (line.length() > 0 || lineOverflow) {
        stats.serialRx++;

        JsonDocument req;
        JsonDocument res;

        if (lineOverflow) {
          makeError(res, "", "line_too_long", "serial command exceeds maximum line length");
        } else {
          DeserializationError err = deserializeJson(req, line);
          if (err) {
            makeError(res, "", "invalid_json", err.c_str());
          } else {
            handle(req, res);
          }
        }

        sendJsonSerial(res);
      }
      line = "";
      lineOverflow = false;
    } else {
      if (line.length() < Config::SERIAL_MAX_LINE_LENGTH) {
        line += c;
      } else {
        lineOverflow = true;
      }
    }
  }
}
