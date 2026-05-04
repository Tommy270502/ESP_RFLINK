#include "Utils.h"

String bytesToHex(const uint8_t* data, size_t len) {
  static const char* hex = "0123456789ABCDEF";
  String out;
  out.reserve(len * 2);
  for (size_t i = 0; i < len; i++) {
    out += hex[(data[i] >> 4) & 0x0F];
    out += hex[data[i] & 0x0F];
  }
  return out;
}

bool hexToBytes(const String& hex, uint8_t* out, size_t& outLen, size_t maxLen) {
  String s = hex;
  s.trim();
  if (s.startsWith("0x") || s.startsWith("0X")) s = s.substring(2);
  if (s.length() % 2 != 0) return false;

  size_t len = s.length() / 2;
  if (len > maxLen) return false;

  auto nibble = [](char c) -> int {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
  };

  for (size_t i = 0; i < len; i++) {
    int hi = nibble(s[2 * i]);
    int lo = nibble(s[2 * i + 1]);
    if (hi < 0 || lo < 0) return false;
    out[i] = static_cast<uint8_t>((hi << 4) | lo);
  }

  outLen = len;
  return true;
}

bool parseRadioAddress(const String& value, const String& format, uint8_t* out, size_t len) {
  String v = value;
  String f = format;
  v.trim();
  f.trim();
  f.toLowerCase();

  if (f == "hex" || v.startsWith("0x") || v.startsWith("0X")) {
    size_t outLen = 0;
    if (!hexToBytes(v, out, outLen, len)) return false;
    return outLen == len;
  }

  if (f.length() > 0 && f != "ascii") return false;
  if (static_cast<size_t>(v.length()) != len) return false;

  for (size_t i = 0; i < len; i++) {
    out[i] = static_cast<uint8_t>(v[i]);
  }
  return true;
}

String bytesToPrintableAscii(const uint8_t* data, size_t len) {
  String out;
  out.reserve(len);

  for (size_t i = 0; i < len; i++) {
    if (data[i] < 32 || data[i] > 126) return "";
    out += static_cast<char>(data[i]);
  }

  return out;
}

String datarateToString(rf24_datarate_e r) {
  switch (r) {
    case RF24_250KBPS: return "250kbps";
    case RF24_1MBPS:   return "1mbps";
    case RF24_2MBPS:   return "2mbps";
    default:           return "unknown";
  }
}

String powerToString(rf24_pa_dbm_e p) {
  switch (p) {
    case RF24_PA_MIN:  return "min";
    case RF24_PA_LOW:  return "low";
    case RF24_PA_HIGH: return "high";
    case RF24_PA_MAX:  return "max";
    default:           return "unknown";
  }
}

bool parseDatarate(const String& s, rf24_datarate_e& out) {
  if (s == "250kbps") {
    out = RF24_250KBPS;
    return true;
  }
  if (s == "1mbps") {
    out = RF24_1MBPS;
    return true;
  }
  if (s == "2mbps") {
    out = RF24_2MBPS;
    return true;
  }
  return false;
}

bool parsePower(const String& s, rf24_pa_dbm_e& out) {
  if (s == "min") {
    out = RF24_PA_MIN;
    return true;
  }
  if (s == "low") {
    out = RF24_PA_LOW;
    return true;
  }
  if (s == "high") {
    out = RF24_PA_HIGH;
    return true;
  }
  if (s == "max") {
    out = RF24_PA_MAX;
    return true;
  }
  return false;
}

void sendJsonSerial(const JsonDocument& doc) {
  serializeJson(doc, Serial);
  Serial.println();
}
