#include "RadioService.h"
#include "Config.h"
#include "AppState.h"
#include "Utils.h"
#include <SPI.h>
#include <RF24.h>
#include <ArduinoJson.h>
#include <string.h>

static RF24 radio(Config::PIN_NRF_CE, Config::PIN_NRF_CSN);
static uint8_t rxAddress[Config::RF_ADDRESS_WIDTH] = {
  Config::RF_ADDR_RX[0],
  Config::RF_ADDR_RX[1],
  Config::RF_ADDR_RX[2],
  Config::RF_ADDR_RX[3],
  Config::RF_ADDR_RX[4],
};
static uint8_t txAddress[Config::RF_ADDRESS_WIDTH] = {
  Config::RF_ADDR_TX[0],
  Config::RF_ADDR_TX[1],
  Config::RF_ADDR_TX[2],
  Config::RF_ADDR_TX[3],
  Config::RF_ADDR_TX[4],
};
RadioService radioService;

bool RadioService::begin() {
  SPI.begin(
    Config::PIN_NRF_SCK,
    Config::PIN_NRF_MISO,
    Config::PIN_NRF_MOSI,
    Config::PIN_NRF_CSN
  );

  if (!radio.begin(&SPI)) {
    rfCfg.initialized = false;
    return false;
  }

  rfCfg.initialized = true;
  rfCfg.listening = false;
  applyConfig();
  return startListening();
}

bool RadioService::applyConfig() {
  if (!rfCfg.initialized) return false;

  bool resumeListening = rfCfg.listening;
  radio.stopListening();

  radio.setAddressWidth(Config::RF_ADDRESS_WIDTH);
  radio.setChannel(rfCfg.channel);
  radio.setDataRate(rfCfg.datarate);
  radio.setPALevel(rfCfg.power);
  radio.setPayloadSize(Config::RF_PAYLOAD_MAX);
  radio.setRetries(5, 15);
  radio.setAutoAck(rfCfg.autoAck);
  radio.enableDynamicPayloads();
  radio.enableDynamicAck();

  radio.openWritingPipe(txAddress);
  radio.openReadingPipe(1, rxAddress);

  if (resumeListening) radio.startListening();
  return true;
}

bool RadioService::send(const uint8_t* data, size_t len, bool requireAck) {
  if (!rfCfg.initialized || len == 0 || len > Config::RF_PAYLOAD_MAX) return false;

  bool resumeListening = rfCfg.listening;
  radio.stopListening();
  delayMicroseconds(150);

  bool ok = radio.write(data, len, !requireAck);

  if (resumeListening) radio.startListening();

  if (ok) stats.rfTx++;
  else stats.rfTxFail++;

  return ok;
}

bool RadioService::startListening() {
  if (!rfCfg.initialized) return false;

  rfCfg.listening = true;
  radio.startListening();
  return true;
}

bool RadioService::stopListening() {
  if (!rfCfg.initialized) return false;

  radio.stopListening();
  rfCfg.listening = false;
  return true;
}

bool RadioService::flushRx() {
  if (!rfCfg.initialized) return false;

  radio.flush_rx();
  return true;
}

bool RadioService::flushTx() {
  if (!rfCfg.initialized) return false;

  radio.flush_tx();
  return true;
}

void RadioService::loadAddress(uint8_t* target, const uint8_t* address, size_t len) {
  if (len != Config::RF_ADDRESS_WIDTH) return;
  memcpy(target, address, Config::RF_ADDRESS_WIDTH);
}

bool RadioService::setAddress(uint8_t* target, const uint8_t* address, size_t len) {
  if (len != Config::RF_ADDRESS_WIDTH) return false;
  if (!rfCfg.initialized) return false;

  memcpy(target, address, Config::RF_ADDRESS_WIDTH);
  return applyConfig();
}

bool RadioService::setRxAddress(const uint8_t* address, size_t len) {
  return setAddress(rxAddress, address, len);
}

bool RadioService::setTxAddress(const uint8_t* address, size_t len) {
  return setAddress(txAddress, address, len);
}

void RadioService::loadRxAddress(const uint8_t* address, size_t len) {
  loadAddress(rxAddress, address, len);
}

void RadioService::loadTxAddress(const uint8_t* address, size_t len) {
  loadAddress(txAddress, address, len);
}

bool RadioService::copyRxAddress(uint8_t* out, size_t len) const {
  if (len != Config::RF_ADDRESS_WIDTH) return false;
  memcpy(out, rxAddress, Config::RF_ADDRESS_WIDTH);
  return true;
}

bool RadioService::copyTxAddress(uint8_t* out, size_t len) const {
  if (len != Config::RF_ADDRESS_WIDTH) return false;
  memcpy(out, txAddress, Config::RF_ADDRESS_WIDTH);
  return true;
}

bool RadioService::isChipConnected() {
  return rfCfg.initialized && radio.isChipConnected();
}

void RadioService::fillConfig(JsonObject data) {
  data["initialized"] = rfCfg.initialized;
  data["chip_connected"] = isChipConnected();
  data["channel"] = rfCfg.channel;
  data["datarate"] = datarateToString(rfCfg.datarate);
  data["power"] = powerToString(rfCfg.power);
  data["auto_ack"] = rfCfg.autoAck;
  data["listening"] = rfCfg.listening;
  data["payload_max"] = Config::RF_PAYLOAD_MAX;
  data["address_width"] = Config::RF_ADDRESS_WIDTH;
  data["rx_address_hex"] = bytesToHex(rxAddress, Config::RF_ADDRESS_WIDTH);
  data["tx_address_hex"] = bytesToHex(txAddress, Config::RF_ADDRESS_WIDTH);

  String rxAscii = bytesToPrintableAscii(rxAddress, Config::RF_ADDRESS_WIDTH);
  String txAscii = bytesToPrintableAscii(txAddress, Config::RF_ADDRESS_WIDTH);
  if (rxAscii.length() > 0) data["rx_address_ascii"] = rxAscii;
  if (txAscii.length() > 0) data["tx_address_ascii"] = txAscii;
}

void RadioService::poll() {
  if (!rfCfg.initialized || !rfCfg.listening) return;

  uint8_t packetsRead = 0;
  while (radio.available() && packetsRead < Config::RF_MAX_PACKETS_PER_POLL) {
    uint8_t payload[Config::RF_PAYLOAD_MAX];
    uint8_t len = radio.getDynamicPayloadSize();

    if (len == 0 || len > Config::RF_PAYLOAD_MAX) {
      radio.flush_rx();
      stats.rfRxInvalid++;
      return;
    }

    radio.read(payload, len);
    packetsRead++;
    stats.rfRx++;

    if (onPacket) onPacket(payload, len);

    JsonDocument doc;
    doc["type"] = "packet";
    doc["source"] = "rf";
    JsonObject data = doc["data"].to<JsonObject>();
    data["len"] = len;
    data["hex"] = bytesToHex(payload, len);
    data["uptime_ms"] = millis();
    sendJsonSerial(doc);
  }
}

void RadioService::setPacketCallback(void (*callback)(const uint8_t* data, size_t len)) {
  onPacket = callback;
}
