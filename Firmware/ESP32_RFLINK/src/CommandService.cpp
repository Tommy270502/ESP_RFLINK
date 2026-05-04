#include "CommandService.h"
#include "Config.h"
#include "AppState.h"
#include "Utils.h"
#include "RadioService.h"
#include "BridgeService.h"
#include <WiFi.h>
#include <string.h>

CommandService commandService;

static void fillStats(JsonObject data) {
  data["rf_rx"] = stats.rfRx;
  data["rf_tx"] = stats.rfTx;
  data["rf_tx_fail"] = stats.rfTxFail;
  data["rf_rx_invalid"] = stats.rfRxInvalid;
  data["ws_rx"] = stats.wsRx;
  data["serial_rx"] = stats.serialRx;
}

static void fillWifiStatus(JsonObject data) {
  const bool apMode = WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA;
  data["ap_mode"] = apMode;
  data["ssid"] = Config::AP_SSID;
  data["ip"] = WiFi.softAPIP().toString();
  data["clients"] = WiFi.softAPgetStationNum();
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

  JsonObject statData = data["stats"].to<JsonObject>();
  fillStats(statData);
}

static void fillCapabilities(JsonObject data) {
  data["product"] = "WirelessDevBridge";
  data["fw"] = Config::FW_VERSION;
  data["protocol"] = Config::PROTOCOL_VERSION;
  data["role"] = Config::DEVICE_ROLE_NAME;

  JsonObject transports = data["transports"].to<JsonObject>();
  transports["usb_serial_jsonl"] = true;
  transports["http_json"] = true;
  transports["websocket_json"] = true;
  transports["ble_gatt"] = false;

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
}

static void handleRfConfig(JsonDocument& req, JsonDocument& res) {
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
    rfCfg.channel = static_cast<uint8_t>(ch);
  }

  String datarateString;
  if (!req["datarate"].isNull()) {
    if (!readStringArg(req, "datarate", datarateString)) {
      commandService.makeError(res, "rf_config", "invalid_arg", "datarate must be a string");
      return;
    }

    rf24_datarate_e datarate;
    if (!parseDatarate(datarateString, datarate)) {
      commandService.makeError(res, "rf_config", "invalid_datarate", "datarate must be 250kbps, 1mbps, or 2mbps");
      return;
    }
    rfCfg.datarate = datarate;
  }

  String powerString;
  if (!req["power"].isNull()) {
    if (!readStringArg(req, "power", powerString)) {
      commandService.makeError(res, "rf_config", "invalid_arg", "power must be a string");
      return;
    }

    rf24_pa_dbm_e power;
    if (!parsePower(powerString, power)) {
      commandService.makeError(res, "rf_config", "invalid_power", "power must be min, low, high, or max");
      return;
    }
    rfCfg.power = power;
  }

  JsonVariant autoAckArg = req["auto_ack"];
  if (!autoAckArg.isNull()) {
    if (!autoAckArg.is<bool>()) {
      commandService.makeError(res, "rf_config", "invalid_arg", "auto_ack must be true or false");
      return;
    }
    rfCfg.autoAck = autoAckArg.as<bool>();
  }

  if (!radioService.applyConfig()) {
    commandService.makeError(res, "rf_config", "radio_not_initialized", "radio not initialized");
    return;
  }

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

  JsonObject data = commandService.makeOk(res, "bridge");
  bridgeService.fillStatus(data);
}

void CommandService::handle(JsonDocument& req, JsonDocument& res) {
  const char* cmd = req["cmd"] | "";

  if (strlen(cmd) == 0) {
    makeError(res, "", "missing_cmd", "cmd is required");
    return;
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
    data["free_heap"] = ESP.getFreeHeap();
    data["heap_size"] = ESP.getHeapSize();
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
