#include "BleService.h"
#include "Config.h"
#include "AppState.h"
#include "CommandService.h"
#include "SettingsService.h"
#include "Utils.h"

#if BLE_ENABLED
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#endif

BleService bleService;

#if BLE_ENABLED
static BLECharacteristic* txCharacteristic = nullptr;
static BLEServer* bleServer = nullptr;

class BridgeBleServerCallbacks : public BLEServerCallbacks {
public:
  void onConnect(BLEServer*) override {
    bleService.setConnected(true);
  }

  void onDisconnect(BLEServer*) override {
    bleService.setConnected(false);
    BLEDevice::startAdvertising();
  }
};

class BridgeBleRxCallbacks : public BLECharacteristicCallbacks {
public:
  void onWrite(BLECharacteristic* characteristic) override {
    std::string value = characteristic->getValue();
    if (value.empty()) return;

    bleService.appendRx(reinterpret_cast<const uint8_t*>(value.data()), value.length());
  }
};
#endif

void BleService::begin() {
#if BLE_ENABLED
  if (!Config::BLE_ENABLE) return;

  BLEDevice::init(settingsService.bleName());
  BLEDevice::setMTU(185);

  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new BridgeBleServerCallbacks());

  BLEService* service = bleServer->createService(Config::BLE_SERVICE_UUID);

  txCharacteristic = service->createCharacteristic(
    Config::BLE_TX_UUID,
    BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ
  );
  txCharacteristic->addDescriptor(new BLE2902());
  txCharacteristic->setValue("ready\n");

  BLECharacteristic* rxCharacteristic = service->createCharacteristic(
    Config::BLE_RX_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  rxCharacteristic->setCallbacks(new BridgeBleRxCallbacks());

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(Config::BLE_SERVICE_UUID);
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  bleEnabled = true;
#endif
}

void BleService::poll() {
  if (!bleEnabled) return;
  processRxBuffer();
}

bool BleService::enabled() const {
  return bleEnabled;
}

bool BleService::connected() const {
  return bleConnected;
}

void BleService::setConnected(bool isConnected) {
  bleConnected = isConnected;
}

void BleService::fillStatus(JsonObject data) const {
  data["enabled"] = bleEnabled;
  data["connected"] = bleConnected;
  data["name"] = settingsService.bleName();
  data["service_uuid"] = Config::BLE_SERVICE_UUID;
  data["rx_uuid"] = Config::BLE_RX_UUID;
  data["tx_uuid"] = Config::BLE_TX_UUID;
}

void BleService::notifyJson(const JsonDocument& doc) {
  String line;
  serializeJson(doc, line);
  notifyLine(line);
}

void BleService::notifyRfPacket(const uint8_t* data, size_t len) {
  if (!bleEnabled || !bleConnected) return;

  JsonDocument doc;
  doc["type"] = "packet";
  doc["source"] = "rf";
  JsonObject payload = doc["data"].to<JsonObject>();
  payload["len"] = len;
  payload["hex"] = bytesToHex(data, len);
  payload["uptime_ms"] = millis();
  notifyJson(doc);
}

void BleService::appendRx(const uint8_t* data, size_t len) {
  if (!bleEnabled) return;

  for (size_t i = 0; i < len; i++) {
    if (rxBuffer.length() >= Config::BLE_MAX_LINE_LENGTH) {
      rxOverflow = true;
      continue;
    }
    rxBuffer += static_cast<char>(data[i]);
  }
}

void BleService::processRxBuffer() {
  if (rxOverflow) {
    JsonDocument res;
    commandService.makeError(res, "", "line_too_long", "BLE command exceeds maximum line length");
    notifyJson(res);
    rxBuffer = "";
    rxOverflow = false;
    return;
  }

  while (true) {
    int newline = rxBuffer.indexOf('\n');
    if (newline < 0) break;

    String line = rxBuffer.substring(0, newline);
    rxBuffer = rxBuffer.substring(newline + 1);
    line.trim();
    if (line.length() > 0) handleLine(line);
  }

  String candidate = rxBuffer;
  candidate.trim();
  if (candidate.startsWith("{") && candidate.endsWith("}")) {
    rxBuffer = "";
    handleLine(candidate);
  }
}

void BleService::handleLine(const String& line) {
  stats.bleRx++;

  JsonDocument req;
  JsonDocument res;

  DeserializationError err = deserializeJson(req, line);
  if (err) {
    commandService.makeError(res, "", "invalid_json", err.c_str());
  } else {
    commandService.handle(req, res, CommandTransport::Ble);
  }

  notifyJson(res);
}

void BleService::notifyLine(const String& line) {
#if BLE_ENABLED
  if (!bleEnabled || !bleConnected || txCharacteristic == nullptr) return;

  String out = line;
  if (!out.endsWith("\n")) out += '\n';

  size_t offset = 0;
  while (offset < static_cast<size_t>(out.length())) {
    size_t chunkLen = min(Config::BLE_NOTIFY_CHUNK_SIZE, static_cast<size_t>(out.length()) - offset);
    txCharacteristic->setValue(reinterpret_cast<uint8_t*>(const_cast<char*>(out.c_str() + offset)), chunkLen);
    txCharacteristic->notify();
    offset += chunkLen;
    delay(4);
  }
#else
  (void)line;
#endif
}
