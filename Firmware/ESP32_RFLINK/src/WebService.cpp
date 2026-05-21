#include "WebService.h"
#include "Config.h"
#include "AppState.h"
#include "Utils.h"
#include "CommandService.h"
#include "SettingsService.h"
#include "WebUi.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <string.h>

static WebServer server(Config::HTTP_PORT);
static WebSocketsServer ws(Config::WS_PORT);
WebService webService;

static void sendJsonHttp(const JsonDocument& doc) {
  String out;
  serializeJson(doc, out);
  const char* code = doc["error"]["code"] | "";
  int status = doc["ok"].as<bool>() ? 200 : (strcmp(code, "auth_required") == 0 ? 401 : 400);
  server.send(status, "application/json", out);
}

static void injectHttpAuth(JsonDocument& req) {
  if (!req["auth"].isNull()) return;

  String token = server.header("X-WDB-Token");
  if (token.length() > 0) req["auth"] = token;
}

static void runCommand(
  JsonDocument& req,
  JsonDocument& res,
  const char* forcedCmd = nullptr,
  CommandTransport transport = CommandTransport::Http
) {
  if (forcedCmd != nullptr) req["cmd"] = forcedCmd;
  if (transport == CommandTransport::Http) injectHttpAuth(req);
  commandService.handle(req, res, transport);
}

static void handleJsonCommandHttp(const char* forcedCmd = nullptr) {
  JsonDocument req;
  JsonDocument res;

  DeserializationError err = deserializeJson(req, server.arg("plain"));
  if (err) {
    commandService.makeError(res, forcedCmd == nullptr ? "" : forcedCmd, "invalid_json", err.c_str());
    sendJsonHttp(res);
    return;
  }

  runCommand(req, res, forcedCmd);
  sendJsonHttp(res);
  webService.broadcastStatus();
}

static void handleSimpleCommandHttp(const char* cmd) {
  JsonDocument req;
  JsonDocument res;
  runCommand(req, res, cmd);
  sendJsonHttp(res);
}

static void onWsEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_CONNECTED) {
    webService.broadcastStatus();
    return;
  }

  if (type == WStype_TEXT) {
    stats.wsRx++;

    JsonDocument req;
    JsonDocument res;

    DeserializationError err = deserializeJson(req, payload, length);
    if (err) {
      commandService.makeError(res, "", "invalid_json", err.c_str());
    } else {
      commandService.handle(req, res, CommandTransport::WebSocket);
    }

    String out;
    serializeJson(res, out);
    ws.sendTXT(num, out);
    webService.broadcastStatus();
  }
}

void WebService::begin() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(settingsService.apSsid(), settingsService.apPass(), 1, 0, 10);

  const char* headers[] = {"X-WDB-Token"};
  server.collectHeaders(headers, 1);
  setupRoutes();
  server.begin();

  ws.begin();
  ws.onEvent(onWsEvent);
}

void WebService::poll() {
  server.handleClient();
  ws.loop();
}

void WebService::broadcastRfPacket(const uint8_t* data, size_t len) {
  JsonDocument doc;
  doc["type"] = "packet";
  doc["source"] = "rf";
  JsonObject payload = doc["data"].to<JsonObject>();
  payload["len"] = len;
  payload["hex"] = bytesToHex(data, len);
  payload["uptime_ms"] = millis();

  String msg;
  serializeJson(doc, msg);
  ws.broadcastTXT(msg);
}

void WebService::broadcastStatus() {
  JsonDocument req;
  JsonDocument res;
  JsonDocument evt;

  req["cmd"] = "status";
  commandService.handle(req, res);

  evt["type"] = "status";
  evt["data"].set(res["data"]);

  String msg;
  serializeJson(evt, msg);
  ws.broadcastTXT(msg);
}

void WebService::setupRoutes() {
  server.on("/", HTTP_GET, []() {
    server.send_P(200, "text/html", WEB_UI_HTML);
  });

  server.on("/api/status", HTTP_GET, []() {
    handleSimpleCommandHttp("status");
  });

  server.on("/api/self_test", HTTP_GET, []() {
    handleSimpleCommandHttp("self_test");
  });

  server.on("/api/command", HTTP_POST, []() {
    handleJsonCommandHttp();
  });

  server.on("/api/rf/config", HTTP_GET, []() {
    handleSimpleCommandHttp("rf_get_config");
  });

  server.on("/api/rf/config", HTTP_POST, []() {
    handleJsonCommandHttp("rf_config");
  });

  server.on("/api/rf/send", HTTP_POST, []() {
    handleJsonCommandHttp("rf_send");
  });

  server.on("/api/rf/listen/start", HTTP_POST, []() {
    JsonDocument req;
    JsonDocument res;
    runCommand(req, res, "rf_start_listen");
    sendJsonHttp(res);
    webService.broadcastStatus();
  });

  server.on("/api/rf/listen/stop", HTTP_POST, []() {
    JsonDocument req;
    JsonDocument res;
    runCommand(req, res, "rf_stop_listen");
    sendJsonHttp(res);
    webService.broadcastStatus();
  });

  server.on("/api/rf/flush_rx", HTTP_POST, []() {
    JsonDocument req;
    JsonDocument res;
    runCommand(req, res, "rf_flush_rx");
    sendJsonHttp(res);
    webService.broadcastStatus();
  });

  server.on("/api/rf/flush_tx", HTTP_POST, []() {
    JsonDocument req;
    JsonDocument res;
    runCommand(req, res, "rf_flush_tx");
    sendJsonHttp(res);
    webService.broadcastStatus();
  });

  server.on("/api/bridge", HTTP_POST, []() {
    handleJsonCommandHttp("bridge");
  });

  server.onNotFound([]() {
    JsonDocument res;
    commandService.makeError(res, "", "not_found", "not found");
    sendJsonHttp(res);
  });
}
