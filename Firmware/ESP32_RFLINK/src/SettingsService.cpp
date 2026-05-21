#include "SettingsService.h"
#include "AppState.h"
#include "BridgeService.h"
#include "Config.h"
#include "RadioService.h"
#include "Utils.h"
#include <Preferences.h>

SettingsService settingsService;

static const char* SETTINGS_NAMESPACE = "wdb";

void SettingsService::begin() {
  applyDefaults();

  Preferences prefs;
  if (!prefs.begin(SETTINGS_NAMESPACE, true)) return;

  settingsLoaded = prefs.getBool("valid", false);
  if (settingsLoaded) {
    currentDeviceName = prefs.getString("dev_name", currentDeviceName);
    currentApSsid = prefs.getString("ap_ssid", currentApSsid);
    currentApPass = prefs.getString("ap_pass", currentApPass);
    currentBleName = prefs.getString("ble_name", currentBleName);
    currentAuthRequired = prefs.getBool("auth_req", currentAuthRequired);
    currentAuthToken = prefs.getString("auth_token", currentAuthToken);

    rfCfg.channel = prefs.getUChar("rf_ch", rfCfg.channel);
    String datarate = prefs.getString("rf_rate", datarateToString(rfCfg.datarate));
    rf24_datarate_e parsedDatarate;
    if (parseDatarate(datarate, parsedDatarate)) rfCfg.datarate = parsedDatarate;

    String power = prefs.getString("rf_power", powerToString(rfCfg.power));
    rf24_pa_dbm_e parsedPower;
    if (parsePower(power, parsedPower)) rfCfg.power = parsedPower;

    rfCfg.autoAck = prefs.getBool("rf_ack", rfCfg.autoAck);
    rfCfg.bridgeRfToWifi = prefs.getBool("br_wifi", rfCfg.bridgeRfToWifi);
    rfCfg.bridgeRfToBle = prefs.getBool("br_ble", rfCfg.bridgeRfToBle);

    uint8_t address[Config::RF_ADDRESS_WIDTH];
    size_t addressLen = 0;
    String rxHex = prefs.getString("rx_hex", "");
    if (hexToBytes(rxHex, address, addressLen, sizeof(address)) && addressLen == sizeof(address)) {
      radioService.loadRxAddress(address, sizeof(address));
    }

    String txHex = prefs.getString("tx_hex", "");
    if (hexToBytes(txHex, address, addressLen, sizeof(address)) && addressLen == sizeof(address)) {
      radioService.loadTxAddress(address, sizeof(address));
    }
  }

  prefs.end();
}

void SettingsService::applyDefaults() {
  currentDeviceName = "WirelessDevBridge";
  currentApSsid = Config::AP_SSID;
  currentApPass = Config::AP_PASS;
  currentBleName = Config::BLE_NAME;
  currentAuthToken = "";
  currentAuthRequired = false;

  rfCfg.channel = 76;
  rfCfg.datarate = RF24_1MBPS;
  rfCfg.power = RF24_PA_LOW;
  rfCfg.autoAck = true;
  rfCfg.listening = true;
  rfCfg.bridgeRfToWifi = true;
  rfCfg.bridgeRfToBle = true;

  uint8_t rx[Config::RF_ADDRESS_WIDTH] = {
    Config::RF_ADDR_RX[0],
    Config::RF_ADDR_RX[1],
    Config::RF_ADDR_RX[2],
    Config::RF_ADDR_RX[3],
    Config::RF_ADDR_RX[4],
  };
  uint8_t tx[Config::RF_ADDRESS_WIDTH] = {
    Config::RF_ADDR_TX[0],
    Config::RF_ADDR_TX[1],
    Config::RF_ADDR_TX[2],
    Config::RF_ADDR_TX[3],
    Config::RF_ADDR_TX[4],
  };
  radioService.loadRxAddress(rx, sizeof(rx));
  radioService.loadTxAddress(tx, sizeof(tx));
}

bool SettingsService::save() {
  Preferences prefs;
  if (!prefs.begin(SETTINGS_NAMESPACE, false)) return false;

  uint8_t rx[Config::RF_ADDRESS_WIDTH];
  uint8_t tx[Config::RF_ADDRESS_WIDTH];
  radioService.copyRxAddress(rx, sizeof(rx));
  radioService.copyTxAddress(tx, sizeof(tx));

  prefs.putBool("valid", true);
  prefs.putString("dev_name", currentDeviceName);
  prefs.putString("ap_ssid", currentApSsid);
  prefs.putString("ap_pass", currentApPass);
  prefs.putString("ble_name", currentBleName);
  prefs.putBool("auth_req", currentAuthRequired);
  prefs.putString("auth_token", currentAuthToken);
  prefs.putUChar("rf_ch", rfCfg.channel);
  prefs.putString("rf_rate", datarateToString(rfCfg.datarate));
  prefs.putString("rf_power", powerToString(rfCfg.power));
  prefs.putBool("rf_ack", rfCfg.autoAck);
  prefs.putString("rx_hex", bytesToHex(rx, sizeof(rx)));
  prefs.putString("tx_hex", bytesToHex(tx, sizeof(tx)));
  prefs.putBool("br_wifi", rfCfg.bridgeRfToWifi);
  prefs.putBool("br_ble", rfCfg.bridgeRfToBle);
  prefs.end();

  settingsLoaded = true;
  settingsDirty = false;
  return true;
}

bool SettingsService::reset() {
  Preferences prefs;
  if (!prefs.begin(SETTINGS_NAMESPACE, false)) return false;
  prefs.clear();
  prefs.end();

  applyDefaults();
  if (rfCfg.initialized) radioService.applyConfig();
  settingsLoaded = false;
  settingsDirty = false;
  needsReboot = true;
  return true;
}

const char* SettingsService::deviceName() const {
  return currentDeviceName.c_str();
}

const char* SettingsService::apSsid() const {
  return currentApSsid.c_str();
}

const char* SettingsService::apPass() const {
  return currentApPass.c_str();
}

const char* SettingsService::bleName() const {
  return currentBleName.c_str();
}

bool SettingsService::setDeviceName(const String& value) {
  if (!validName(value, 32)) return false;
  currentDeviceName = value;
  settingsDirty = true;
  return true;
}

bool SettingsService::setApSsid(const String& value) {
  if (!validName(value, 32)) return false;
  currentApSsid = value;
  settingsDirty = true;
  needsReboot = true;
  return true;
}

bool SettingsService::setApPass(const String& value) {
  if (value.length() < 8 || value.length() > 63) return false;
  currentApPass = value;
  settingsDirty = true;
  needsReboot = true;
  return true;
}

bool SettingsService::setBleName(const String& value) {
  if (!validName(value, 32)) return false;
  currentBleName = value;
  settingsDirty = true;
  needsReboot = true;
  return true;
}

bool SettingsService::setAuthRequired(bool value) {
  currentAuthRequired = value;
  settingsDirty = true;
  return true;
}

bool SettingsService::setAuthToken(const String& value) {
  if (value.length() > 64) return false;
  currentAuthToken = value;
  settingsDirty = true;
  return true;
}

bool SettingsService::authRequired() const {
  return currentAuthRequired;
}

bool SettingsService::tokenConfigured() const {
  return currentAuthToken.length() > 0;
}

bool SettingsService::checkAuth(const char* token) const {
  if (!currentAuthRequired) return true;
  if (currentAuthToken.length() == 0 || token == nullptr) return false;
  return currentAuthToken == token;
}

bool SettingsService::dirty() const {
  return settingsDirty;
}

bool SettingsService::rebootRequired() const {
  return needsReboot;
}

bool SettingsService::loadedFromNvs() const {
  return settingsLoaded;
}

void SettingsService::markDirty() {
  settingsDirty = true;
}

void SettingsService::fillDevice(JsonObject data) const {
  data["product"] = "WirelessDevBridge";
  data["name"] = currentDeviceName;
  data["role"] = Config::DEVICE_ROLE_NAME;
  data["ap_ssid"] = currentApSsid;
  data["ble_name"] = currentBleName;
}

void SettingsService::fillSecurity(JsonObject data) const {
  data["auth_required"] = currentAuthRequired;
  data["token_configured"] = tokenConfigured();
  data["http_header"] = "X-WDB-Token";
  data["json_field"] = "auth";
}

void SettingsService::fillStorage(JsonObject data) const {
  data["namespace"] = SETTINGS_NAMESPACE;
  data["loaded_from_nvs"] = settingsLoaded;
  data["dirty"] = settingsDirty;
  data["reboot_required"] = needsReboot;
}

void SettingsService::fillSettings(JsonObject data) const {
  data["loaded_from_nvs"] = settingsLoaded;
  data["dirty"] = settingsDirty;
  data["reboot_required"] = needsReboot;

  JsonObject effective = data["effective"].to<JsonObject>();
  JsonObject device = effective["device"].to<JsonObject>();
  fillDevice(device);

  JsonObject rf = effective["rf"].to<JsonObject>();
  radioService.fillConfig(rf);

  JsonObject bridge = effective["bridge"].to<JsonObject>();
  bridgeService.fillStatus(bridge);

  JsonObject security = effective["security"].to<JsonObject>();
  fillSecurity(security);

  JsonObject persisted = data["persisted"].to<JsonObject>();
  persisted["available"] = settingsLoaded;
  persisted["namespace"] = SETTINGS_NAMESPACE;
  persisted["contains_secret"] = tokenConfigured();
}

bool SettingsService::validName(const String& value, size_t maxLen) const {
  return value.length() > 0 && value.length() <= maxLen;
}
