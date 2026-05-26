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
  bool bridgeRfToBle = true;
};

struct PacketStats {
  uint32_t rfRx = 0;
  uint32_t rfTx = 0;
  uint32_t rfTxAttempts = 0;
  uint32_t rfTxFail = 0;
  uint32_t rfRxInvalid = 0;
  uint32_t wsRx = 0;
  uint32_t bleRx = 0;
  uint32_t serialRx = 0;
  uint32_t lastPacketMs = 0;
  uint8_t lastPacketLen = 0;
};

static constexpr size_t EVENT_LOG_CAPACITY = 32;

struct EventLogEntry {
  uint32_t timestampMs = 0;
  char type[16] = {};
  char detail[64] = {};
};

class EventLog {
public:
  void add(const char* type, const char* detail);
  size_t count() const { return entryCount; }
  const EventLogEntry& at(size_t index) const;

private:
  EventLogEntry entries[EVENT_LOG_CAPACITY];
  size_t head = 0;
  size_t entryCount = 0;
};

extern RadioConfig rfCfg;
extern PacketStats stats;
extern String lastErrorCode;
extern String lastErrorMessage;
extern EventLog eventLog;
