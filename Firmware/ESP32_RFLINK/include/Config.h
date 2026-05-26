#pragma once
#include <Arduino.h>

#ifndef RF_DEFAULT_RX_ADDR
#define RF_DEFAULT_RX_ADDR "NODE1"
#endif

#ifndef RF_DEFAULT_TX_ADDR
#define RF_DEFAULT_TX_ADDR "NODE2"
#endif

#ifndef DEVICE_ROLE
#define DEVICE_ROLE "generic"
#endif

#ifndef WIFI_AP_SSID
#define WIFI_AP_SSID "WirelessDev-Bridge"
#endif

#ifndef WIFI_AP_PASS
#define WIFI_AP_PASS "12345678"
#endif

#ifndef BLE_ENABLED
#define BLE_ENABLED 1
#endif

#ifndef BLE_DEVICE_NAME
#define BLE_DEVICE_NAME "WirelessDev-Bridge"
#endif

#ifndef BUILD_DATE
#define BUILD_DATE __DATE__
#endif

#ifndef BUILD_PROFILE
#define BUILD_PROFILE "dev"
#endif

#ifndef GIT_SHA
#define GIT_SHA ""
#endif

static constexpr uint8_t SETTINGS_SCHEMA_VERSION = 1;

namespace Config {
  // Adjust these GPIOs for the final PCB routing.
  static constexpr uint8_t PIN_NRF_CE   = 45;
  static constexpr uint8_t PIN_NRF_CSN  = 15;
  static constexpr uint8_t PIN_NRF_SCK  = 14;
  static constexpr uint8_t PIN_NRF_MOSI = 13;
  static constexpr uint8_t PIN_NRF_MISO = 12;
  static constexpr uint8_t PIN_NRF_IRQ = 18;
  static constexpr uint8_t PIN_LED_Rx   = 16;
  static constexpr uint8_t PIN_LED_Tx   = 17;
  static constexpr uint8_t PIN_LED      = PIN_LED_Tx;

  static constexpr const char* FW_VERSION = "0.1.0-v1";
  static constexpr const char* PROTOCOL_VERSION = "1.1";
  static constexpr const char* DEVICE_ROLE_NAME = DEVICE_ROLE;
  static constexpr const char* AP_SSID    = WIFI_AP_SSID;
  static constexpr const char* AP_PASS    = WIFI_AP_PASS;
  static constexpr bool BLE_ENABLE = BLE_ENABLED != 0;
  static constexpr const char* BLE_NAME = BLE_DEVICE_NAME;

  static constexpr uint16_t HTTP_PORT = 80;
  static constexpr uint16_t WS_PORT   = 81;

  static constexpr size_t SERIAL_MAX_LINE_LENGTH = 512;
  static constexpr size_t RF_PAYLOAD_MAX = 32;
  static constexpr uint8_t RF_ADDRESS_WIDTH = 5;
  static constexpr uint8_t RF_MAX_PACKETS_PER_POLL = 4;
  static constexpr size_t BLE_MAX_LINE_LENGTH = 512;
  static constexpr size_t BLE_NOTIFY_CHUNK_SIZE = 180;

  static constexpr const char* BLE_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
  static constexpr const char* BLE_RX_UUID      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e";
  static constexpr const char* BLE_TX_UUID      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

  // nRF24 addresses are fixed-width byte arrays. These defaults are printable
  // for developer usability, but they are still sent as 5 raw address bytes.
  static constexpr uint8_t RF_ADDR_RX[6] = RF_DEFAULT_RX_ADDR;
  static constexpr uint8_t RF_ADDR_TX[6] = RF_DEFAULT_TX_ADDR;
}
