#pragma once
#include <Arduino.h>
#include <RF24.h>

struct RadioConfig {
  uint8_t channel = 76;
  rf24_datarate_e datarate = RF24_1MBPS;
  rf24_pa_dbm_e power = RF24_PA_LOW;
  bool autoAck = true;
  bool listening = true;
  bool initialized = false;
  bool bridgeRfToWifi = true;
};

struct PacketStats {
  uint32_t rfRx = 0;
  uint32_t rfTx = 0;
  uint32_t rfTxFail = 0;
  uint32_t rfRxInvalid = 0;
  uint32_t wsRx = 0;
  uint32_t serialRx = 0;
};

extern RadioConfig rfCfg;
extern PacketStats stats;
