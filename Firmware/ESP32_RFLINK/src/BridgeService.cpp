#include "BridgeService.h"
#include "AppState.h"
#include "WebService.h"

BridgeService bridgeService;

void BridgeService::begin() {
  // Future BLE bridging should be routed through this service, not RadioService.
}

void BridgeService::handleRfPacket(const uint8_t* data, size_t len) {
  if (!rfCfg.bridgeRfToWifi) return;

  webService.broadcastRfPacket(data, len);
}

void BridgeService::setRfToWifiEnabled(bool enabled) {
  rfCfg.bridgeRfToWifi = enabled;
}

bool BridgeService::rfToWifiEnabled() const {
  return rfCfg.bridgeRfToWifi;
}

void BridgeService::fillStatus(JsonObject data) const {
  data["rf_to_wifi"] = rfCfg.bridgeRfToWifi;
  data["wifi_to_rf"] = true;
  data["ble_available"] = false;
}
