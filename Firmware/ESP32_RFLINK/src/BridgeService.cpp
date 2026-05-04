#include "BridgeService.h"
#include "AppState.h"
#include "BleService.h"
#include "Config.h"
#include "WebService.h"

BridgeService bridgeService;

void BridgeService::begin() {
  // Future BLE bridging should be routed through this service, not RadioService.
}

void BridgeService::handleRfPacket(const uint8_t* data, size_t len) {
  if (rfCfg.bridgeRfToWifi) {
    webService.broadcastRfPacket(data, len);
  }

  if (rfCfg.bridgeRfToBle) {
    bleService.notifyRfPacket(data, len);
  }
}

void BridgeService::setRfToWifiEnabled(bool enabled) {
  rfCfg.bridgeRfToWifi = enabled;
}

void BridgeService::setRfToBleEnabled(bool enabled) {
  rfCfg.bridgeRfToBle = enabled;
}

bool BridgeService::rfToWifiEnabled() const {
  return rfCfg.bridgeRfToWifi;
}

bool BridgeService::rfToBleEnabled() const {
  return rfCfg.bridgeRfToBle;
}

void BridgeService::fillStatus(JsonObject data) const {
  data["rf_to_wifi"] = rfCfg.bridgeRfToWifi;
  data["rf_to_ble"] = rfCfg.bridgeRfToBle;
  data["wifi_to_rf"] = true;
  data["ble_to_rf"] = Config::BLE_ENABLE;
  data["ble_available"] = Config::BLE_ENABLE;
}
